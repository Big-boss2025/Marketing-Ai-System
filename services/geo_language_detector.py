import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import re
import json
import pytz
from collections import Counter
import requests

logger = logging.getLogger(__name__)

class GeoLanguageDetector:
    """Smart Geo-Location, Language Detection and Optimal Timing System"""
    
    def __init__(self):
        # Language detection patterns
        self.language_patterns = {
            'arabic': {
                'patterns': [
                    r'[\u0600-\u06FF]',  # Arabic Unicode range
                    r'[\u0750-\u077F]',  # Arabic Supplement
                    r'[\uFB50-\uFDFF]',  # Arabic Presentation Forms-A
                    r'[\uFE70-\uFEFF]'   # Arabic Presentation Forms-B
                ],
                'keywords': [
                    'في', 'من', 'إلى', 'على', 'عن', 'مع', 'هذا', 'هذه', 'التي', 'الذي',
                    'كان', 'كانت', 'يكون', 'تكون', 'أن', 'إن', 'لكن', 'ولكن', 'أو', 'أم'
                ],
                'countries': [
                    'مصر', 'السعودية', 'الإمارات', 'الكويت', 'قطر', 'البحرين', 'عمان',
                    'الأردن', 'لبنان', 'سوريا', 'العراق', 'فلسطين', 'المغرب', 'الجزائر',
                    'تونس', 'ليبيا', 'السودان', 'اليمن'
                ]
            },
            'english': {
                'patterns': [r'[a-zA-Z]'],
                'keywords': [
                    'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
                    'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during'
                ],
                'countries': [
                    'usa', 'uk', 'canada', 'australia', 'new zealand', 'south africa',
                    'ireland', 'scotland', 'wales', 'england', 'britain'
                ]
            },
            'french': {
                'patterns': [r'[àâäéèêëïîôöùûüÿç]'],
                'keywords': [
                    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou',
                    'mais', 'donc', 'car', 'ni', 'or', 'dans', 'sur', 'avec', 'pour'
                ],
                'countries': ['france', 'belgium', 'switzerland', 'canada', 'morocco']
            },
            'spanish': {
                'patterns': [r'[áéíóúñü¿¡]'],
                'keywords': [
                    'el', 'la', 'los', 'las', 'un', 'una', 'y', 'o', 'pero', 'en',
                    'con', 'por', 'para', 'de', 'del', 'al', 'que', 'se', 'no'
                ],
                'countries': ['spain', 'mexico', 'argentina', 'colombia', 'peru']
            },
            'german': {
                'patterns': [r'[äöüß]'],
                'keywords': [
                    'der', 'die', 'das', 'ein', 'eine', 'und', 'oder', 'aber', 'in',
                    'auf', 'mit', 'für', 'von', 'zu', 'an', 'bei', 'nach', 'über'
                ],
                'countries': ['germany', 'austria', 'switzerland']
            }
        }
        
        # Country timezone mapping
        self.country_timezones = {
            # Arabic countries
            'egypt': 'Africa/Cairo',
            'saudi_arabia': 'Asia/Riyadh',
            'uae': 'Asia/Dubai',
            'kuwait': 'Asia/Kuwait',
            'qatar': 'Asia/Qatar',
            'bahrain': 'Asia/Bahrain',
            'oman': 'Asia/Muscat',
            'jordan': 'Asia/Amman',
            'lebanon': 'Asia/Beirut',
            'syria': 'Asia/Damascus',
            'iraq': 'Asia/Baghdad',
            'palestine': 'Asia/Gaza',
            'morocco': 'Africa/Casablanca',
            'algeria': 'Africa/Algiers',
            'tunisia': 'Africa/Tunis',
            'libya': 'Africa/Tripoli',
            'sudan': 'Africa/Khartoum',
            'yemen': 'Asia/Aden',
            
            # English countries
            'usa': 'America/New_York',
            'uk': 'Europe/London',
            'canada': 'America/Toronto',
            'australia': 'Australia/Sydney',
            'new_zealand': 'Pacific/Auckland',
            'south_africa': 'Africa/Johannesburg',
            'ireland': 'Europe/Dublin',
            
            # Other major countries
            'france': 'Europe/Paris',
            'germany': 'Europe/Berlin',
            'spain': 'Europe/Madrid',
            'italy': 'Europe/Rome',
            'russia': 'Europe/Moscow',
            'china': 'Asia/Shanghai',
            'japan': 'Asia/Tokyo',
            'india': 'Asia/Kolkata',
            'brazil': 'America/Sao_Paulo',
            'mexico': 'America/Mexico_City'
        }
        
        # Optimal posting times by country/region
        self.optimal_posting_times = {
            'middle_east': {
                'weekdays': ['19:00', '20:00', '21:00', '22:00'],
                'weekends': ['14:00', '15:00', '19:00', '20:00', '21:00'],
                'peak_days': ['Thursday', 'Friday', 'Saturday'],
                'avoid_times': ['05:00-08:00', '12:00-14:00']  # Prayer times consideration
            },
            'north_america': {
                'weekdays': ['18:00', '19:00', '20:00', '21:00'],
                'weekends': ['10:00', '11:00', '14:00', '15:00', '19:00'],
                'peak_days': ['Tuesday', 'Wednesday', 'Thursday'],
                'avoid_times': ['02:00-06:00', '09:00-11:00']
            },
            'europe': {
                'weekdays': ['17:00', '18:00', '19:00', '20:00'],
                'weekends': ['11:00', '12:00', '15:00', '16:00', '19:00'],
                'peak_days': ['Tuesday', 'Wednesday', 'Thursday'],
                'avoid_times': ['02:00-07:00', '09:00-11:00']
            },
            'asia_pacific': {
                'weekdays': ['19:00', '20:00', '21:00', '22:00'],
                'weekends': ['10:00', '11:00', '14:00', '15:00', '20:00'],
                'peak_days': ['Wednesday', 'Thursday', 'Friday'],
                'avoid_times': ['02:00-06:00', '12:00-14:00']
            }
        }
        
        # Platform-specific timing adjustments
        self.platform_timing_adjustments = {
            'tiktok': {
                'peak_hours': ['18:00', '19:00', '20:00', '21:00'],
                'best_days': ['Tuesday', 'Thursday', 'Friday'],
                'avoid_hours': ['02:00-08:00', '10:00-12:00']
            },
            'instagram': {
                'peak_hours': ['11:00', '13:00', '17:00', '19:00'],
                'best_days': ['Tuesday', 'Wednesday', 'Friday'],
                'avoid_hours': ['03:00-08:00', '22:00-24:00']
            },
            'youtube': {
                'peak_hours': ['14:00', '15:00', '16:00', '17:00'],
                'best_days': ['Thursday', 'Friday', 'Saturday'],
                'avoid_hours': ['02:00-09:00', '23:00-01:00']
            },
            'twitter': {
                'peak_hours': ['09:00', '12:00', '15:00', '18:00'],
                'best_days': ['Tuesday', 'Wednesday', 'Thursday'],
                'avoid_hours': ['02:00-06:00', '22:00-24:00']
            },
            'facebook': {
                'peak_hours': ['13:00', '15:00', '19:00', '20:00'],
                'best_days': ['Wednesday', 'Thursday', 'Friday'],
                'avoid_hours': ['02:00-08:00', '23:00-01:00']
            }
        }
        
        # Cultural considerations
        self.cultural_considerations = {
            'middle_east': {
                'ramadan_adjustments': {
                    'iftar_time': '18:00-20:00',
                    'suhoor_time': '02:00-04:00',
                    'peak_activity': '20:00-02:00'
                },
                'prayer_times': ['05:00', '12:30', '15:30', '18:00', '19:30'],
                'weekend': ['Friday', 'Saturday'],
                'avoid_content': ['alcohol', 'pork', 'inappropriate_imagery']
            },
            'western': {
                'weekend': ['Saturday', 'Sunday'],
                'lunch_break': '12:00-13:00',
                'dinner_time': '18:00-20:00',
                'late_night': '22:00-02:00'
            },
            'asia_pacific': {
                'weekend': ['Saturday', 'Sunday'],
                'lunch_break': '12:00-14:00',
                'dinner_time': '18:00-20:00',
                'cultural_holidays': 'varies_by_country'
            }
        }
    
    def detect_language(self, text: str) -> Dict:
        """Detect the primary language of the text"""
        try:
            if not text or len(text.strip()) < 3:
                return {
                    'language': 'unknown',
                    'confidence': 0.0,
                    'detected_languages': []
                }
            
            text_lower = text.lower()
            language_scores = {}
            
            # Score each language
            for lang, data in self.language_patterns.items():
                score = 0
                
                # Pattern matching
                for pattern in data['patterns']:
                    matches = len(re.findall(pattern, text))
                    score += matches * 2
                
                # Keyword matching
                for keyword in data['keywords']:
                    if keyword in text_lower:
                        score += 3
                
                # Country name matching
                for country in data['countries']:
                    if country in text_lower:
                        score += 5
                
                language_scores[lang] = score
            
            # Determine primary language
            if not language_scores or max(language_scores.values()) == 0:
                return {
                    'language': 'unknown',
                    'confidence': 0.0,
                    'detected_languages': []
                }
            
            primary_language = max(language_scores, key=language_scores.get)
            max_score = language_scores[primary_language]
            total_score = sum(language_scores.values())
            
            confidence = max_score / total_score if total_score > 0 else 0.0
            
            # Sort languages by score
            sorted_languages = sorted(
                language_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            return {
                'language': primary_language,
                'confidence': min(confidence, 1.0),
                'detected_languages': [
                    {'language': lang, 'score': score} 
                    for lang, score in sorted_languages if score > 0
                ]
            }
            
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return {
                'language': 'unknown',
                'confidence': 0.0,
                'detected_languages': []
            }
    
    def detect_country_from_text(self, text: str) -> Dict:
        """Detect country/region from text content"""
        try:
            text_lower = text.lower()
            country_mentions = {}
            
            # Check for explicit country mentions
            for lang_data in self.language_patterns.values():
                for country in lang_data['countries']:
                    if country in text_lower:
                        country_mentions[country] = country_mentions.get(country, 0) + 1
            
            # Check for currency mentions
            currency_patterns = {
                'usd': ['dollar', '$', 'usd'],
                'eur': ['euro', '€', 'eur'],
                'gbp': ['pound', '£', 'gbp'],
                'aed': ['dirham', 'aed'],
                'sar': ['riyal', 'sar'],
                'egp': ['جنيه', 'egp']
            }
            
            detected_currencies = []
            for currency, patterns in currency_patterns.items():
                for pattern in patterns:
                    if pattern in text_lower:
                        detected_currencies.append(currency)
            
            # Determine most likely country
            if country_mentions:
                primary_country = max(country_mentions, key=country_mentions.get)
                confidence = country_mentions[primary_country] / sum(country_mentions.values())
            else:
                primary_country = 'unknown'
                confidence = 0.0
            
            return {
                'country': primary_country,
                'confidence': confidence,
                'country_mentions': country_mentions,
                'detected_currencies': detected_currencies,
                'region': self.get_region_from_country(primary_country)
            }
            
        except Exception as e:
            logger.error(f"Error detecting country: {str(e)}")
            return {
                'country': 'unknown',
                'confidence': 0.0,
                'country_mentions': {},
                'detected_currencies': [],
                'region': 'unknown'
            }
    
    def get_region_from_country(self, country: str) -> str:
        """Get region from country"""
        region_mapping = {
            # Middle East
            'egypt': 'middle_east', 'saudi_arabia': 'middle_east', 'uae': 'middle_east',
            'kuwait': 'middle_east', 'qatar': 'middle_east', 'bahrain': 'middle_east',
            'oman': 'middle_east', 'jordan': 'middle_east', 'lebanon': 'middle_east',
            'syria': 'middle_east', 'iraq': 'middle_east', 'palestine': 'middle_east',
            'morocco': 'middle_east', 'algeria': 'middle_east', 'tunisia': 'middle_east',
            'libya': 'middle_east', 'sudan': 'middle_east', 'yemen': 'middle_east',
            
            # North America
            'usa': 'north_america', 'canada': 'north_america', 'mexico': 'north_america',
            
            # Europe
            'uk': 'europe', 'france': 'europe', 'germany': 'europe', 'spain': 'europe',
            'italy': 'europe', 'ireland': 'europe',
            
            # Asia Pacific
            'australia': 'asia_pacific', 'new_zealand': 'asia_pacific', 'japan': 'asia_pacific',
            'china': 'asia_pacific', 'india': 'asia_pacific'
        }
        
        return region_mapping.get(country, 'unknown')
    
    def get_optimal_posting_times(self, country: str, platform: str, 
                                content_type: str = 'general') -> Dict:
        """Get optimal posting times for specific country and platform"""
        try:
            region = self.get_region_from_country(country)
            
            # Get base timing for region
            region_timing = self.optimal_posting_times.get(region, 
                self.optimal_posting_times['middle_east'])
            
            # Get platform-specific adjustments
            platform_timing = self.platform_timing_adjustments.get(platform, {})
            
            # Get timezone for country
            timezone = self.country_timezones.get(country, 'UTC')
            
            # Combine and optimize times
            optimal_times = self.combine_timing_data(region_timing, platform_timing)
            
            # Add cultural considerations
            cultural_data = self.cultural_considerations.get(region, {})
            
            return {
                'success': True,
                'country': country,
                'region': region,
                'platform': platform,
                'timezone': timezone,
                'optimal_times': optimal_times,
                'cultural_considerations': cultural_data,
                'next_optimal_time': self.calculate_next_optimal_time(
                    optimal_times, timezone
                ),
                'weekly_schedule': self.generate_weekly_schedule(
                    optimal_times, timezone, platform
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting optimal posting times: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def combine_timing_data(self, region_timing: Dict, platform_timing: Dict) -> Dict:
        """Combine region and platform timing data"""
        combined = region_timing.copy()
        
        if platform_timing:
            # Intersect peak hours
            if 'peak_hours' in platform_timing:
                region_hours = set(region_timing.get('weekdays', []))
                platform_hours = set(platform_timing['peak_hours'])
                combined['optimal_hours'] = list(region_hours.intersection(platform_hours))
                
                if not combined['optimal_hours']:
                    combined['optimal_hours'] = platform_timing['peak_hours']
            
            # Combine best days
            if 'best_days' in platform_timing:
                region_days = set(region_timing.get('peak_days', []))
                platform_days = set(platform_timing['best_days'])
                combined['best_days'] = list(region_days.intersection(platform_days))
                
                if not combined['best_days']:
                    combined['best_days'] = platform_timing['best_days']
        
        return combined
    
    def calculate_next_optimal_time(self, optimal_times: Dict, timezone_str: str) -> Dict:
        """Calculate the next optimal posting time"""
        try:
            tz = pytz.timezone(timezone_str)
            now = datetime.now(tz)
            
            # Get optimal hours
            optimal_hours = optimal_times.get('optimal_hours', 
                optimal_times.get('weekdays', ['19:00']))
            
            # Find next optimal time
            for hour_str in optimal_hours:
                hour, minute = map(int, hour_str.split(':'))
                
                # Try today first
                target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if target_time > now:
                    return {
                        'datetime': target_time.isoformat(),
                        'local_time': target_time.strftime('%H:%M'),
                        'day': target_time.strftime('%A'),
                        'hours_from_now': (target_time - now).total_seconds() / 3600
                    }
            
            # If no time today, try tomorrow
            tomorrow = now + timedelta(days=1)
            hour_str = optimal_hours[0]
            hour, minute = map(int, hour_str.split(':'))
            target_time = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            return {
                'datetime': target_time.isoformat(),
                'local_time': target_time.strftime('%H:%M'),
                'day': target_time.strftime('%A'),
                'hours_from_now': (target_time - now).total_seconds() / 3600
            }
            
        except Exception as e:
            logger.error(f"Error calculating next optimal time: {str(e)}")
            return {
                'datetime': datetime.utcnow().isoformat(),
                'local_time': '19:00',
                'day': 'Today',
                'hours_from_now': 1
            }
    
    def generate_weekly_schedule(self, optimal_times: Dict, timezone_str: str, 
                               platform: str) -> List[Dict]:
        """Generate a weekly posting schedule"""
        try:
            tz = pytz.timezone(timezone_str)
            now = datetime.now(tz)
            
            # Get optimal configuration
            weekday_times = optimal_times.get('weekdays', ['19:00'])
            weekend_times = optimal_times.get('weekends', ['15:00', '19:00'])
            best_days = optimal_times.get('best_days', ['Tuesday', 'Thursday', 'Friday'])
            
            schedule = []
            
            # Generate schedule for next 7 days
            for i in range(7):
                target_date = now + timedelta(days=i)
                day_name = target_date.strftime('%A')
                
                # Determine if it's a weekend
                is_weekend = day_name in ['Friday', 'Saturday'] if 'middle_east' in str(optimal_times) else day_name in ['Saturday', 'Sunday']
                
                # Choose appropriate times
                times = weekend_times if is_weekend else weekday_times
                
                # Determine priority
                priority = 'high' if day_name in best_days else 'medium'
                
                for time_str in times:
                    hour, minute = map(int, time_str.split(':'))
                    post_time = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    schedule.append({
                        'date': target_date.strftime('%Y-%m-%d'),
                        'day': day_name,
                        'time': time_str,
                        'datetime': post_time.isoformat(),
                        'priority': priority,
                        'is_weekend': is_weekend,
                        'platform': platform
                    })
            
            return schedule
            
        except Exception as e:
            logger.error(f"Error generating weekly schedule: {str(e)}")
            return []
    
    def analyze_audience_geography(self, audience_data: List[Dict]) -> Dict:
        """Analyze audience geographical distribution"""
        try:
            if not audience_data:
                return {
                    'success': False,
                    'error': 'No audience data provided'
                }
            
            country_distribution = Counter()
            language_distribution = Counter()
            timezone_distribution = Counter()
            
            for user in audience_data:
                # Extract country info
                country = user.get('country', 'unknown')
                if country != 'unknown':
                    country_distribution[country] += 1
                    
                    # Map to timezone
                    timezone = self.country_timezones.get(country, 'UTC')
                    timezone_distribution[timezone] += 1
                
                # Extract language info
                language = user.get('language', 'unknown')
                if language != 'unknown':
                    language_distribution[language] += 1
            
            total_users = len(audience_data)
            
            # Calculate percentages
            country_percentages = {
                country: (count / total_users) * 100 
                for country, count in country_distribution.items()
            }
            
            language_percentages = {
                language: (count / total_users) * 100 
                for language, count in language_distribution.items()
            }
            
            # Determine primary segments
            primary_country = country_distribution.most_common(1)[0][0] if country_distribution else 'unknown'
            primary_language = language_distribution.most_common(1)[0][0] if language_distribution else 'unknown'
            primary_timezone = timezone_distribution.most_common(1)[0][0] if timezone_distribution else 'UTC'
            
            return {
                'success': True,
                'total_users': total_users,
                'primary_country': primary_country,
                'primary_language': primary_language,
                'primary_timezone': primary_timezone,
                'country_distribution': dict(country_distribution),
                'language_distribution': dict(language_distribution),
                'timezone_distribution': dict(timezone_distribution),
                'country_percentages': country_percentages,
                'language_percentages': language_percentages,
                'recommendations': self.generate_audience_recommendations(
                    primary_country, primary_language, country_percentages
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing audience geography: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_audience_recommendations(self, primary_country: str, 
                                        primary_language: str, 
                                        country_percentages: Dict) -> Dict:
        """Generate recommendations based on audience analysis"""
        recommendations = {
            'content_language': primary_language,
            'primary_timezone': self.country_timezones.get(primary_country, 'UTC'),
            'posting_strategy': [],
            'content_localization': [],
            'cultural_considerations': []
        }
        
        # Posting strategy recommendations
        if primary_country in self.country_timezones:
            region = self.get_region_from_country(primary_country)
            recommendations['posting_strategy'].append(
                f"Focus on {region} optimal posting times"
            )
        
        # Multi-country strategy
        significant_countries = [
            country for country, percentage in country_percentages.items() 
            if percentage > 10
        ]
        
        if len(significant_countries) > 1:
            recommendations['posting_strategy'].append(
                "Consider multi-timezone posting strategy"
            )
            recommendations['content_localization'].append(
                "Create region-specific content variations"
            )
        
        # Cultural considerations
        if primary_country in ['egypt', 'saudi_arabia', 'uae', 'kuwait', 'qatar']:
            recommendations['cultural_considerations'].extend([
                "Consider Islamic holidays and prayer times",
                "Use culturally appropriate imagery",
                "Respect local customs and traditions"
            ])
        
        return recommendations
    
    def get_timezone_info(self, country: str) -> Dict:
        """Get detailed timezone information for a country"""
        try:
            timezone_str = self.country_timezones.get(country, 'UTC')
            tz = pytz.timezone(timezone_str)
            now = datetime.now(tz)
            
            return {
                'country': country,
                'timezone': timezone_str,
                'current_time': now.isoformat(),
                'current_hour': now.hour,
                'current_day': now.strftime('%A'),
                'utc_offset': now.strftime('%z'),
                'is_dst': bool(now.dst()),
                'region': self.get_region_from_country(country)
            }
            
        except Exception as e:
            logger.error(f"Error getting timezone info: {str(e)}")
            return {
                'country': country,
                'timezone': 'UTC',
                'current_time': datetime.utcnow().isoformat(),
                'current_hour': datetime.utcnow().hour,
                'current_day': datetime.utcnow().strftime('%A'),
                'utc_offset': '+0000',
                'is_dst': False,
                'region': 'unknown'
            }

# Global geo-language detector instance
geo_language_detector = GeoLanguageDetector()

