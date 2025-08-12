from src.models.base import db, BaseModel
from datetime import datetime
import json

class KeywordCategory(db.Model):
    """Categories for organizing keywords"""
    __tablename__ = 'keyword_categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    name_ar = Column(String(100), nullable=False)
    description = Column(Text)
    description_ar = Column(Text)
    color = Column(String(20), default='#3B82F6')
    icon = Column(String(50))

    # Category settings
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    keywords = relationship("Keyword", back_populates="category")
    hashtags = relationship("Hashtag", back_populates="category")

    def save(self):
        """Save category to database"""
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'name_ar': self.name_ar,
            'description': self.description,
            'description_ar': self.description_ar,
            'color': self.color,
            'icon': self.icon,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'keyword_count': len(self.keywords),
            'hashtag_count': len(self.hashtags),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Keyword(BaseModel):
    """Keywords for content optimization and SEO"""
    __tablename__ = 'keywords'

    keyword = db.Column(db.String(200), nullable=False)
    keyword_ar = db.Column(db.String(200))  # Arabic translation
    category_id = db.Column(db.Integer, db.ForeignKey('keyword_categories.id'), nullable=True)

    # Keyword metrics
    search_volume = db.Column(db.Integer, default=0)  # Monthly search volume
    competition_level = db.Column(db.String(20), default='medium')  # low, medium, high
    difficulty_score = db.Column(db.Float, default=50.0)  # 0-100 scale
    cpc = db.Column(db.Float, default=0.0)  # Cost per click

    # Usage tracking
    usage_count = db.Column(db.Integer, default=0)
    last_used_at = db.Column(db.DateTime, nullable=True)
    performance_score = db.Column(db.Float, default=0.0)  # Based on content performance

    # Keyword properties
    language = db.Column(db.String(10), default='ar')
    region = db.Column(db.String(10), default='ME')  # Middle East
    industry = db.Column(db.String(100))
    intent_type = db.Column(db.String(20), default='informational')  # informational, commercial, transactional

    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_trending = db.Column(db.Boolean, default=False)
    is_seasonal = db.Column(db.Boolean, default=False)

    # Related keywords (JSON)
    related_keywords = db.Column(db.Text)  # JSON array of related keywords
    synonyms = db.Column(db.Text)  # JSON array of synonyms

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("KeywordCategory", back_populates="keywords")
    content_keywords = relationship("ContentKeyword", back_populates="keyword")

    def __init__(self, keyword, **kwargs):
        self.keyword = keyword.lower().strip()

        # Set optional parameters
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def add_related_keyword(self, related_keyword):
        """Add a related keyword"""
        related = json.loads(self.related_keywords) if self.related_keywords else []
        if related_keyword not in related:
            related.append(related_keyword)
            self.related_keywords = json.dumps(related)

    def add_synonym(self, synonym):
        """Add a synonym"""
        synonyms = json.loads(self.synonyms) if self.synonyms else []
        if synonym not in synonyms:
            synonyms.append(synonym)
            self.synonyms = json.dumps(synonyms)

    def update_usage(self):
        """Update usage statistics"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def calculate_relevance_score(self, content_text):
        """Calculate relevance score for given content"""
        content_lower = content_text.lower()

        # Base score for exact match
        score = 0.0
        if self.keyword in content_lower:
            score += 10.0

        # Score for related keywords
        if self.related_keywords:
            related = json.loads(self.related_keywords)
            for related_kw in related:
                if related_kw.lower() in content_lower:
                    score += 5.0

        # Score for synonyms
        if self.synonyms:
            synonyms = json.loads(self.synonyms)
            for synonym in synonyms:
                if synonym.lower() in content_lower:
                    score += 3.0

        return min(score, 100.0)

    # --- Added Methods from changes ---
    def get_related_keywords(self):
        """Get related keywords as list"""
        if self.related_keywords:
            try:
                return json.loads(self.related_keywords)
            except:
                return []
        return []

    def set_related_keywords(self, keywords_list):
        """Set related keywords from list"""
        self.related_keywords = json.dumps(keywords_list)

    def get_synonyms(self):
        """Get synonyms as list"""
        if self.synonyms:
            try:
                return json.loads(self.synonyms)
            except:
                return []
        return []

    def set_synonyms(self, synonyms_list):
        """Set synonyms from list"""
        self.synonyms = json.dumps(synonyms_list)
    # --- End of Added Methods ---

    def save(self):
        """Save keyword to database"""
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'keyword': self.keyword,
            'keyword_ar': self.keyword_ar,
            'category_id': self.category_id,
            'search_volume': self.search_volume,
            'competition_level': self.competition_level,
            'difficulty_score': self.difficulty_score,
            'cpc': self.cpc,
            'usage_count': self.usage_count,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'performance_score': self.performance_score,
            'language': self.language,
            'region': self.region,
            'industry': self.industry,
            'intent_type': self.intent_type,
            'is_active': self.is_active,
            'is_trending': self.is_trending,
            'is_seasonal': self.is_seasonal,
            'related_keywords': json.loads(self.related_keywords) if self.related_keywords else [],
            'synonyms': json.loads(self.synonyms) if self.synonyms else [],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Hashtag(BaseModel):
    """Hashtags for social media optimization"""
    __tablename__ = 'hashtags'

    hashtag = db.Column(db.String(200), nullable=False)  # Without # symbol
    category_id = db.Column(db.Integer, db.ForeignKey('keyword_categories.id'), nullable=True)

    # Hashtag metrics
    popularity_score = db.Column(db.Float, default=0.0)  # 0-100 scale
    usage_frequency = db.Column(db.Integer, default=0)  # How often it's used across platforms
    engagement_rate = db.Column(db.Float, default=0.0)  # Average engagement rate
    reach_potential = db.Column(db.Integer, default=0)  # Estimated reach

    # Platform-specific data (JSON)
    platform_data = db.Column(db.Text)  # JSON object with platform-specific metrics

    # Usage tracking
    usage_count = db.Column(db.Integer, default=0)
    last_used_at = db.Column(db.DateTime, nullable=True)
    performance_score = db.Column(db.Float, default=0.0)

    # Hashtag properties
    language = db.Column(db.String(10), default='ar')
    region = db.Column(db.String(10), default='ME')
    industry = db.Column(db.String(100))
    hashtag_type = db.Column(db.String(20), default='general')  # general, branded, trending, event

    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_trending = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)  # Banned on any platform
    is_seasonal = db.Column(db.Boolean, default=False)

    # Related hashtags (JSON)
    related_hashtags = db.Column(db.Text)  # JSON array of related hashtags

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("KeywordCategory", back_populates="hashtags")
    content_hashtags = relationship("ContentHashtag", back_populates="hashtag")

    def __init__(self, hashtag, **kwargs):
        # Remove # symbol and clean hashtag
        self.hashtag = hashtag.replace('#', '').lower().strip()

        # Set optional parameters
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def get_formatted_hashtag(self):
        """Get hashtag with # symbol"""
        return f"#{self.hashtag}"

    def add_related_hashtag(self, related_hashtag):
        """Add a related hashtag"""
        related = json.loads(self.related_hashtags) if self.related_hashtags else []
        clean_hashtag = related_hashtag.replace('#', '').lower().strip()
        if clean_hashtag not in related:
            related.append(clean_hashtag)
            self.related_hashtags = json.dumps(related)

    def update_platform_data(self, platform, data):
        """Update platform-specific data"""
        platform_data = json.loads(self.platform_data) if self.platform_data else {}
        platform_data[platform] = data
        self.platform_data = json.dumps(platform_data)

    def get_platform_data(self, platform):
        """Get platform-specific data"""
        if not self.platform_data:
            return {}
        platform_data = json.loads(self.platform_data)
        return platform_data.get(platform, {})

    def update_usage(self):
        """Update usage statistics"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def calculate_effectiveness_score(self, platform='instagram'):
        """Calculate effectiveness score for a specific platform"""
        platform_data = self.get_platform_data(platform)

        # Base score from popularity
        score = self.popularity_score * 0.4

        # Add engagement rate score
        score += self.engagement_rate * 0.3

        # Add platform-specific score
        if platform_data:
            platform_engagement = platform_data.get('engagement_rate', 0)
            score += platform_engagement * 0.3

        return min(score, 100.0)

    def save(self):
        """Save hashtag to database"""
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'hashtag': self.hashtag,
            'formatted_hashtag': self.get_formatted_hashtag(),
            'category_id': self.category_id,
            'popularity_score': self.popularity_score,
            'usage_frequency': self.usage_frequency,
            'engagement_rate': self.engagement_rate,
            'reach_potential': self.reach_potential,
            'platform_data': json.loads(self.platform_data) if self.platform_data else {},
            'usage_count': self.usage_count,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'performance_score': self.performance_score,
            'language': self.language,
            'region': self.region,
            'industry': self.industry,
            'hashtag_type': self.hashtag_type,
            'is_active': self.is_active,
            'is_trending': self.is_trending,
            'is_banned': self.is_banned,
            'is_seasonal': self.is_seasonal,
            'related_hashtags': json.loads(self.related_hashtags) if self.related_hashtags else [],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class ContentKeyword(db.Model):
    """Association between content and keywords"""
    __tablename__ = 'content_keywords'

    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    keyword_id = Column(Integer, ForeignKey('keywords.id'), nullable=False)
    relevance_score = Column(Float, default=0.0)  # How relevant the keyword is to the content
    density = Column(Float, default=0.0)  # Keyword density in the content
    position = Column(Integer, default=0)  # Position in content (for ranking)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    content = relationship("Content")
    keyword = relationship("Keyword", back_populates="content_keywords")

    def save(self):
        """Save content keyword to database"""
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'content_id': self.content_id,
            'keyword_id': self.keyword_id,
            'relevance_score': self.relevance_score,
            'density': self.density,
            'position': self.position,
            'created_at': self.created_at.isoformat()
        }

class ContentHashtag(db.Model):
    """Association between content and hashtags"""
    __tablename__ = 'content_hashtags'

    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    hashtag_id = Column(Integer, ForeignKey('hashtags.id'), nullable=False)
    platform = Column(String(20), nullable=False)  # Platform where hashtag is used
    position = Column(Integer, default=0)  # Position in hashtag list
    performance_score = Column(Float, default=0.0)  # Performance of this hashtag for this content

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    content = relationship("Content")
    hashtag = relationship("Hashtag", back_populates="content_hashtags")

    def save(self):
        """Save content hashtag to database"""
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'content_id': self.content_id,
            'hashtag_id': self.hashtag_id,
            'platform': self.platform,
            'position': self.position,
            'performance_score': self.performance_score,
            'created_at': self.created_at.isoformat()
        }

class TrendingTopic(db.Model):
    """Trending topics and keywords"""
    __tablename__ = 'trending_topics'

    id = Column(Integer, primary_key=True)
    topic = Column(String(200), nullable=False)
    topic_ar = Column(String(200))

    # Trend metrics
    trend_score = Column(Float, default=0.0)  # 0-100 scale
    search_volume = Column(Integer, default=0)
    mention_count = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)

    # Trend properties
    category = Column(String(100))
    region = Column(String(10), default='ME')
    language = Column(String(10), default='ar')
    trend_type = Column(String(20), default='general')  # general, news, entertainment, sports, etc.

    # Platform data (JSON)
    platform_data = Column(Text)  # JSON object with platform-specific trend data

    # Timing
    started_trending_at = Column(DateTime, nullable=False)
    peak_time = Column(DateTime, nullable=True)
    ended_trending_at = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Manually verified trend

    # Related data (JSON)
    related_keywords = Column(Text)  # JSON array of related keywords
    related_hashtags = Column(Text)  # JSON array of related hashtags

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, topic, **kwargs):
        self.topic = topic.strip()
        self.started_trending_at = datetime.utcnow()

        # Set optional parameters
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def add_related_keyword(self, keyword):
        """Add a related keyword"""
        related = json.loads(self.related_keywords) if self.related_keywords else []
        if keyword not in related:
            related.append(keyword)
            self.related_keywords = json.dumps(related)

    def add_related_hashtag(self, hashtag):
        """Add a related hashtag"""
        related = json.loads(self.related_hashtags) if self.related_hashtags else []
        clean_hashtag = hashtag.replace('#', '').lower().strip()
        if clean_hashtag not in related:
            related.append(clean_hashtag)
            self.related_hashtags = json.dumps(related)

    def update_platform_data(self, platform, data):
        """Update platform-specific trend data"""
        platform_data = json.loads(self.platform_data) if self.platform_data else {}
        platform_data[platform] = data
        self.platform_data = json.dumps(platform_data)

    def is_currently_trending(self):
        """Check if topic is currently trending"""
        if not self.is_active:
            return False

        if self.ended_trending_at and datetime.utcnow() > self.ended_trending_at:
            return False

        # Consider trending if started within last 7 days and no end date
        if not self.ended_trending_at:
            days_since_start = (datetime.utcnow() - self.started_trending_at).days
            return days_since_start <= 7

        return True

    def save(self):
        """Save trending topic to database"""
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'topic': self.topic,
            'topic_ar': self.topic_ar,
            'trend_score': self.trend_score,
            'search_volume': self.search_volume,
            'mention_count': self.mention_count,
            'engagement_rate': self.engagement_rate,
            'category': self.category,
            'region': self.region,
            'language': self.language,
            'trend_type': self.trend_type,
            'platform_data': json.loads(self.platform_data) if self.platform_data else {},
            'started_trending_at': self.started_trending_at.isoformat(),
            'peak_time': self.peak_time.isoformat() if self.peak_time else None,
            'ended_trending_at': self.ended_trending_at.isoformat() if self.ended_trending_at else None,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_currently_trending': self.is_currently_trending(),
            'related_keywords': json.loads(self.related_keywords) if self.related_keywords else [],
            'related_hashtags': json.loads(self.related_hashtags) if self.related_hashtags else [],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }