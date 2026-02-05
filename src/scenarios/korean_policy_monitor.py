"""
Real-time Korean Energy Policy Monitor for Climate Scenario Analysis.

This module provides automated monitoring, parsing, and classification
of Korean energy policy announcements with integration into financial models.

Features:
- Automated policy source monitoring (MOTIE, Climate Ministry, etc.)
- Policy announcement parsing and classification
- Real-time scenario updates
- Policy impact assessment
- Integration with climate policy scenario generator

Usage:
    monitor = PolicyMonitor()
    monitor.start_monitoring()
    announcements = monitor.get_recent_announcements(days=30)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
import json
import asyncio
import logging
import re
from enum import Enum
import requests
from bs4 import BeautifulSoup
import feedparser

from .enhanced_climate_policy_generator import PolicyAnnouncement, PolicyType, PolicyImpact


class PolicySource:
    """Represents a policy information source."""
    
    def __init__(
        self,
        name: str,
        url: str,
        source_type: str,
        update_frequency_hours: int,
        selectors: List[str],
        api_key: Optional[str] = None
    ):
        self.name = name
        self.url = url
        self.source_type = source_type  # 'government', 'news', 'rss'
        self.update_frequency_hours = update_frequency_hours
        self.selectors = selectors
        self.api_key = api_key
        self.last_check = datetime.now() - timedelta(hours=update_frequency_hours)
    
    def needs_update(self) -> bool:
        """Check if source needs to be updated."""
        return datetime.now() >= self.last_check + timedelta(hours=self.update_frequency_hours)
    
    def mark_updated(self):
        """Mark source as updated."""
        self.last_check = datetime.now()


class PolicyParser:
    """Parser for extracting policy information from various sources."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Policy keywords for classification
        self.policy_keywords = {
            PolicyType.COAL_PHASE_OUT: [
                "coal phase-out", "coal phaseout", "석탄 폐지", "석탄 감축",
                "powering past coal", "PPCA", "unabated coal", "coal retirement",
                "coal-fired power plant", "발전소 폐쇄"
            ],
            PolicyType.RENEWABLE_TARGET: [
                "renewable target", "renewable energy", "solar", "wind", 
                "재생에너지", "태양광", "풍력", "100gw", "renewable deployment",
                "clean energy"
            ],
            PolicyType.EMISSIONS_REDUCTION: [
                "emissions reduction", "carbon reduction", "nationally determined contribution",
                "ndc", "온실가스 감축", "탄소 감축", "carbon neutrality", "2050"
            ],
            PolicyType.NUCLEAR_EXPANSION: [
                "nuclear expansion", "nuclear power", "원자력", "신규 원전",
                "smr", "small modular reactor", "nuclear deployment"
            ],
            PolicyType.CARBON_PRICING: [
                "carbon pricing", "carbon tax", "emissions trading", "ets",
                "탄소세", "탄소가격", "배출권거래제"
            ],
            PolicyType.INDUSTRIAL_TRANSITION: [
                "industrial transition", "green transformation", "kgx", "k-gx",
                "industry decarbonization", "산업 전환", "녹색성장"
            ]
        }
        
        # Impact level keywords
        self.impact_keywords = {
            PolicyImpact.LOW: [
                "review", "study", "consideration", "제고", "검토"
            ],
            PolicyImpact.MEDIUM: [
                "plan", "target", "goal", "계획", "목표", "strategy"
            ],
            PolicyImpact.HIGH: [
                "commitment", "pledge", "agreement", "약속", "합의", "공약"
            ],
            PolicyImpact.TRANSFORMATIONAL: [
                "phase-out", "ban", "mandatory", "requirement", 
                "의무화", "금지", "전면 폐지"
            ]
        }
    
    def classify_policy_type(self, text: str) -> PolicyType:
        """Classify policy type based on text content."""
        text_lower = text.lower()
        scores = {}
        
        for policy_type, keywords in self.policy_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            scores[policy_type] = score
        
        # Return type with highest score, default to EMISSIONS_REDUCTION
        if max(scores.values()) == 0:
            return PolicyType.EMISSIONS_REDUCTION
        
        return max(scores, key=scores.get)
    
    def assess_impact_level(self, text: str, policy_type: PolicyType) -> PolicyImpact:
        """Assess policy impact level."""
        text_lower = text.lower()
        scores = {}
        
        for impact_level, keywords in self.impact_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            scores[impact_level] = score
        
        # Adjust based on policy type
        if policy_type == PolicyType.COAL_PHASE_OUT:
            if any(word in text_lower for word in ["2040", "2050", "complete", "전면"]):
                scores[PolicyImpact.TRANSFORMATIONAL] += 2
            elif "phase-out" in text_lower:
                scores[PolicyImpact.HIGH] += 2
        elif policy_type == PolicyType.RENEWABLE_TARGET:
            if any(word in text_lower for word in ["100gw", "2030", "accelerated"]):
                scores[PolicyImpact.TRANSFORMATIONAL] += 1
        
        # Return level with highest score
        return max(scores, key=scores.get) if max(scores.values()) > 0 else PolicyImpact.MEDIUM
    
    def extract_metrics(self, text: str, policy_type: PolicyType) -> Dict[str, Any]:
        """Extract quantitative metrics from policy text."""
        metrics = {}
        text_lower = text.lower()
        
        # Extract years
        year_patterns = {
            r"by (\d{4})": "target_year",
            r"(\d{4})년": "target_year",
            r"until (\d{4})": "end_year"
        }
        
        for pattern, key in year_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                year = int(match.group(1))
                if 2020 <= year <= 2060:  # Reasonable range
                    metrics[key] = year
        
        # Extract numerical values
        if policy_type == PolicyType.COAL_PHASE_OUT:
            # Number of plants
            plants_match = re.search(r"(\d+)\s*(?:coal\s*)?plant", text_lower)
            if plants_match:
                metrics["coal_plants_to_close"] = int(plants_match.group(1))
            
            # Coal share percentages
            share_match = re.search(r"coal\s*share\s*(?:of\s*)?(\d+(?:\.\d+)?)", text_lower)
            if share_match:
                metrics["coal_share_target"] = float(share_match.group(1))
        
        elif policy_type == PolicyType.RENEWABLE_TARGET:
            # GW targets
            gw_match = re.search(r"(\d+(?:\.\d+)?)\s*gw", text_lower)
            if gw_match:
                metrics["renewable_target_gw"] = float(gw_match.group(1))
            
            # Percentage targets
            pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", text_lower)
            if pct_match:
                metrics["renewable_target_pct"] = float(pct_match.group(1))
        
        elif policy_type == PolicyType.EMISSIONS_REDUCTION:
            # Emission reduction percentages
            reduction_match = re.search(r"reduc(?:e|tion).*?(\d+(?:\.\d+)?)\s*%", text_lower)
            if reduction_match:
                metrics["emissions_reduction_pct"] = float(reduction_match.group(1))
        
        # Default confidence level based on language
        confidence = 0.7
        if any(word in text_lower for word in ["commitment", "pledge", "약속", "공약"]):
            confidence = 0.9
        elif any(word in text_lower for word in ["plan", "target", "계획", "목표"]):
            confidence = 0.8
        elif any(word in text_lower for word in ["draft", "proposal", "초안", "제안"]):
            confidence = 0.6
        
        metrics["confidence_level"] = confidence
        
        return metrics
    
    def parse_announcement(
        self,
        title: str,
        content: str,
        source: str,
        url: str,
        announcement_date: datetime,
        effective_date: Optional[datetime] = None
    ) -> Optional[PolicyAnnouncement]:
        """Parse a policy announcement into structured format."""
        try:
            # Combine title and content for analysis
            full_text = f"{title} {content}"
            
            # Classify policy type and impact
            policy_type = self.classify_policy_type(full_text)
            impact_level = self.assess_impact_level(full_text, policy_type)
            
            # Extract metrics
            metrics = self.extract_metrics(full_text, policy_type)
            
            # Generate ID
            date_str = announcement_date.strftime("%Y%m%d")
            source_clean = re.sub(r"[^a-zA-Z0-9]", "", source.lower())[:10]
            title_clean = re.sub(r"[^a-zA-Z0-9]", "", title.lower())[:20]
            policy_id = f"{date_str}_{source_clean}_{title_clean}"
            
            # Set effective date (default to 6 months after announcement if not specified)
            if effective_date is None:
                effective_date = announcement_date + timedelta(days=180)
            
            return PolicyAnnouncement(
                id=policy_id,
                title=title.strip(),
                description=content.strip()[:500] + "..." if len(content) > 500 else content.strip(),
                announcement_date=announcement_date,
                effective_date=effective_date,
                policy_type=policy_type,
                impact_level=impact_level,
                source=source,
                url=url,
                metrics=metrics,
                confidence_level=metrics.get("confidence_level", 0.7)
            )
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to parse announcement: {e}")
            return None


class AutomatedPolicyMonitor:
    """
    Automated monitoring system for Korean energy policy announcements.
    
    Continuously monitors various sources and automatically parses new policies.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or Path("config/automated_monitor.json")
        
        # Initialize components
        self.parser = PolicyParser()
        self.sources: List[PolicySource] = []
        self.announcements: List[PolicyAnnouncement] = []
        self.subscribers: List[Callable[[PolicyAnnouncement], None]] = []
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Load configuration
        self._load_configuration()
    
    def _load_configuration(self):
        """Load monitoring configuration."""
        default_config = {
            "sources": [
                {
                    "name": "MOTIE",
                    "url": "https://www.motie.go.kr/motie/ne/nes2/nes2131/nes213101.jsp",
                    "source_type": "government",
                    "update_frequency_hours": 12,
                    "selectors": ["press", "policy", "announcement"],
                    "parser_config": {
                        "title_selector": ".title",
                        "content_selector": ".content",
                        "date_selector": ".date"
                    }
                },
                {
                    "name": "Climate Ministry RSS",
                    "url": "https://www.me.go.kr/home/web/main.do",
                    "source_type": "rss",
                    "update_frequency_hours": 6,
                    "selectors": ["climate", "renewable", "carbon"],
                    "parser_config": {
                        "rss_fields": ["title", "description", "published"]
                    }
                },
                {
                    "name": "Korea Herald Environment",
                    "url": "https://www.koreaherald.com/environment",
                    "source_type": "news",
                    "update_frequency_hours": 8,
                    "selectors": ["energy", "climate", "policy"],
                    "parser_config": {
                        "article_selector": ".article",
                        "title_selector": ".headline",
                        "content_selector": ".article-body",
                        "date_selector": ".date"
                    }
                }
            ],
            "monitoring": {
                "enabled": True,
                "check_interval_minutes": 60,
                "max_retries": 3,
                "timeout_seconds": 30
            }
        }
        
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    config = json.load(f)
            else:
                config = default_config
                self.config_path.parent.mkdir(exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to load config: {e}. Using defaults.")
            config = default_config
        
        # Initialize sources
        self.sources = []
        for source_config in config["sources"]:
            source = PolicySource(
                name=source_config["name"],
                url=source_config["url"],
                source_type=source_config["source_type"],
                update_frequency_hours=source_config["update_frequency_hours"],
                selectors=source_config["selectors"],
                api_key=source_config.get("api_key")
            )
            self.sources.append(source)
        
        self.monitoring_config = config["monitoring"]
    
    def subscribe(self, callback: Callable[[PolicyAnnouncement], None]):
        """Subscribe to new policy announcements."""
        self.subscribers.append(callback)
    
    def _fetch_rss_feed(self, source: PolicySource) -> List[Dict[str, Any]]:
        """Fetch RSS feed entries."""
        try:
            feed = feedparser.parse(source.url)
            entries = []
            
            for entry in feed.entries:
                entries.append({
                    'title': entry.title,
                    'content': getattr(entry, 'description', entry.summary),
                    'url': entry.link,
                    'date': datetime(*getattr(entry, 'published_parsed', datetime.now().timetuple())[:6]),
                    'source': source.name
                })
            
            return entries
            
        except Exception as e:
            self.logger.error(f"Failed to fetch RSS feed from {source.name}: {e}")
            return []
    
    def _fetch_webpage(self, source: PolicySource) -> List[Dict[str, Any]]:
        """Fetch webpage content."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(source.url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for articles/news items
            articles = []
            
            # Generic selectors for news items
            article_selectors = [
                'article', '.news-item', '.press-release', '.announcement',
                '.post', 'tr', 'li'
            ]
            
            for selector in article_selectors:
                items = soup.select(selector)
                if len(items) > 5:  # Found meaningful content
                    for item in items[:10]:  # Limit to recent items
                        try:
                            title_elem = item.select_one('h1, h2, h3, h4, .title, .headline')
                            content_elem = item.select_one('p, .content, .description, .summary')
                            date_elem = item.select_one('.date, .time, .published, datetime')
                            link_elem = item.select_one('a')
                            
                            if title_elem:
                                title = title_elem.get_text().strip()
                                content = content_elem.get_text().strip() if content_elem else ""
                                url = link_elem.get('href') if link_elem else source.url
                                
                                if url.startswith('/'):
                                    from urllib.parse import urljoin
                                    url = urljoin(source.url, url)
                                
                                # Parse date
                                date_text = date_elem.get_text().strip() if date_elem else ""
                                date = datetime.now()
                                if date_text:
                                    try:
                                        # Try different date formats
                                        for fmt in ["%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d", "%b %d, %Y"]:
                                            try:
                                                date = datetime.strptime(date_text, fmt)
                                                break
                                            except ValueError:
                                                continue
                                    except Exception:
                                        pass
                                
                                articles.append({
                                    'title': title,
                                    'content': content,
                                    'url': url,
                                    'date': date,
                                    'source': source.name
                                })
                        except Exception as e:
                            continue
                    
                    if articles:
                        break
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Failed to fetch webpage from {source.name}: {e}")
            return []
    
    def _check_source(self, source: PolicySource) -> List[PolicyAnnouncement]:
        """Check a single source for new announcements."""
        if not source.needs_update():
            return []
        
        self.logger.info(f"Checking source: {source.name}")
        
        try:
            if source.source_type == "rss":
                entries = self._fetch_rss_feed(source)
            else:
                entries = self._fetch_webpage(source)
            
            announcements = []
            for entry in entries:
                # Parse announcement
                announcement = self.parser.parse_announcement(
                    title=entry['title'],
                    content=entry['content'],
                    source=entry['source'],
                    url=entry['url'],
                    announcement_date=entry['date']
                )
                
                if announcement:
                    # Check if already exists
                    if not any(a.id == announcement.id for a in self.announcements):
                        announcements.append(announcement)
                        self.announcements.append(announcement)
            
            source.mark_updated()
            
            if announcements:
                self.logger.info(f"Found {len(announcements)} new announcements from {source.name}")
            
            return announcements
            
        except Exception as e:
            self.logger.error(f"Failed to check source {source.name}: {e}")
            return []
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                new_announcements = []
                
                # Check each source
                for source in self.sources:
                    announcements = self._check_source(source)
                    new_announcements.extend(announcements)
                
                # Notify subscribers
                for announcement in new_announcements:
                    for callback in self.subscribers:
                        try:
                            callback(announcement)
                        except Exception as e:
                            self.logger.error(f"Subscriber callback failed: {e}")
                
                # Wait for next check
                await asyncio.sleep(
                    self.monitoring_config["check_interval_minutes"] * 60
                )
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def start_monitoring(self):
        """Start automated monitoring."""
        if self.is_monitoring:
            self.logger.warning("Monitoring already started")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Started automated policy monitoring")
    
    def stop_monitoring(self):
        """Stop automated monitoring."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
        
        self.logger.info("Stopped automated policy monitoring")
    
    def manual_check(self, source_name: Optional[str] = None) -> List[PolicyAnnouncement]:
        """Manually check for new announcements."""
        announcements = []
        
        sources_to_check = [
            s for s in self.sources 
            if source_name is None or s.name == source_name
        ]
        
        for source in sources_to_check:
            announcements.extend(self._check_source(source))
        
        return announcements
    
    def get_announcements_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get summary of recent announcements."""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent = [a for a in self.announcements if a.announcement_date >= cutoff_date]
        
        # Group by type
        by_type = {}
        for policy_type in PolicyType:
            by_type[policy_type.value] = [
                a for a in recent if a.policy_type == policy_type
            ]
        
        # Group by impact
        by_impact = {}
        for impact_level in PolicyImpact:
            by_impact[impact_level.value] = [
                a for a in recent if a.impact_level == impact_level
            ]
        
        return {
            'total_announcements': len(recent),
            'by_type': {k: len(v) for k, v in by_type.items()},
            'by_impact': {k: len(v) for k, v in by_impact.items()},
            'sources': list(set(a.source for a in recent)),
            'date_range': {
                'start': min(a.announcement_date for a in recent).isoformat() if recent else None,
                'end': max(a.announcement_date for a in recent).isoformat() if recent else None
            }
        }


def create_test_announcements() -> List[PolicyAnnouncement]:
    """Create test policy announcements for demonstration."""
    announcements = []
    
    # Test announcement 1: Coal phase-out
    announcement1 = PolicyAnnouncement(
        id="test_coal_phaseout_2026",
        title="Korea Announces Accelerated Coal Phase-Out Plan",
        description="The government announced today an accelerated plan to phase out coal-fired power plants by 2035, 15 years earlier than previously planned. The commitment includes closing 30 coal plants and converting 10 to clean hydrogen facilities.",
        announcement_date=datetime.now() - timedelta(days=5),
        effective_date=datetime.now() + timedelta(days=90),
        policy_type=PolicyType.COAL_PHASE_OUT,
        impact_level=PolicyImpact.TRANSFORMATIONAL,
        source="Ministry of Trade, Industry and Energy",
        url="https://www.motie.go.kr/press/example1",
        metrics={
            "coal_plants_to_close": 30,
            "target_year": 2035,
            "hydrogen_conversion": 10,
            "confidence_level": 0.85
        },
        confidence_level=0.85
    )
    
    # Test announcement 2: Renewable target
    announcement2 = PolicyAnnouncement(
        id="test_renewable_2026",
        title="New 120 GW Renewable Energy Target by 2030",
        description="The Climate Ministry announced an ambitious new target to install 120 GW of renewable energy capacity by 2030, with solar and wind each accounting for 40 GW and the remaining 40 GW from other sources including biomass and small hydro.",
        announcement_date=datetime.now() - timedelta(days=3),
        effective_date=datetime.now() + timedelta(days=30),
        policy_type=PolicyType.RENEWABLE_TARGET,
        impact_level=PolicyImpact.HIGH,
        source="Ministry of Climate, Energy and Environment",
        url="https://www.me.go.kr/press/example2",
        metrics={
            "renewable_target_gw": 120,
            "target_year": 2030,
            "solar_target": 40,
            "wind_target": 40,
            "confidence_level": 0.8
        },
        confidence_level=0.8
    )
    
    announcements.extend([announcement1, announcement2])
    return announcements


def main():
    """Example usage of the automated policy monitor."""
    # Create monitor
    monitor = AutomatedPolicyMonitor()
    
    # Add test announcements
    test_announcements = create_test_announcements()
    for announcement in test_announcements:
        monitor.announcements.append(announcement)
        print(f"Added test announcement: {announcement.title}")
    
    # Get summary
    summary = monitor.get_announcements_summary(days=30)
    print(f"\nAnnouncements Summary (last 30 days):")
    print(f"Total: {summary['total_announcements']}")
    print(f"By type: {summary['by_type']}")
    print(f"By impact: {summary['by_impact']}")
    
    # Manual check (would normally fetch from sources)
    print("\nPerforming manual check...")
    new_announcements = monitor.manual_check()
    print(f"Found {len(new_announcements)} new announcements")
    
    # Example: Start monitoring (commented out for demo)
    # monitor.start_monitoring()
    # try:
    #     while True:
    #         time.sleep(60)
    # except KeyboardInterrupt:
    #     monitor.stop_monitoring()


if __name__ == "__main__":
    main()