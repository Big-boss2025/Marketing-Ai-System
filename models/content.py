from src.models.base import db, BaseModel
from datetime import datetime
import json
import os

class Content(BaseModel):
    """Content model for managing generated content"""
    __tablename__ = 'contents'

    # User & Task Association
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.String(36), db.ForeignKey('tasks.id'), nullable=True)
    campaign_id = db.Column(db.String(36), db.ForeignKey('campaigns.id'), nullable=True)

    # Content Details
    title = db.Column(db.String(200), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # text, image, video, audio, post, story, etc.
    content_format = db.Column(db.String(20), nullable=True)  # jpg, png, mp4, wav, etc.

    # Content Data
    text_content = db.Column(db.Text, nullable=True)  # For text-based content
    file_path = db.Column(db.String(500), nullable=True)  # For file-based content
    file_size = db.Column(db.Integer, nullable=True)  # File size in bytes

    # Content Metadata (JSON)
    content_metadata = db.Column(db.Text, nullable=True)  # JSON with additional content metadata

    # Generation Details
    generation_prompt = db.Column(db.Text, nullable=True)  # Original prompt used
    generation_model = db.Column(db.String(100), nullable=True)  # AI model used
    generation_parameters = db.Column(db.Text, nullable=True)  # JSON with generation params

    # Quality & Status
    quality_score = db.Column(db.Float, nullable=True)  # AI-generated quality score (0-1)
    status = db.Column(db.String(20), default='generated', nullable=False)  # generated, approved, rejected, published

    # Usage Tracking
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    last_used_at = db.Column(db.DateTime, nullable=True)

    # Social Media Specific
    platforms_used = db.Column(db.Text, nullable=True)  # JSON array of platforms where content was used
    hashtags = db.Column(db.Text, nullable=True)  # JSON array of hashtags
    mentions = db.Column(db.Text, nullable=True)  # JSON array of mentions

    # Performance Metrics (JSON)
    performance_metrics = db.Column(db.Text, nullable=True)  # JSON with engagement metrics

    # Relationships
    user = db.relationship('User', backref='contents')
    task = db.relationship('Task', backref='contents')
    campaign = db.relationship('Campaign', backref='contents')

    def get_metadata(self):
        """Get metadata as dictionary"""
        if self.content_metadata:
            try:
                return json.loads(self.content_metadata)
            except:
                return {}
        return {}

    def set_metadata(self, metadata_dict):
        """Set metadata from dictionary"""
        self.content_metadata = json.dumps(metadata_dict)

    def get_generation_parameters(self):
        """Get generation parameters as dictionary"""
        if self.generation_parameters:
            try:
                return json.loads(self.generation_parameters)
            except:
                return {}
        return {}

    def set_generation_parameters(self, params_dict):
        """Set generation parameters from dictionary"""
        self.generation_parameters = json.dumps(params_dict)

    def get_platforms_used(self):
        """Get platforms used as list"""
        if self.platforms_used:
            try:
                return json.loads(self.platforms_used)
            except:
                return []
        return []

    def set_platforms_used(self, platforms_list):
        """Set platforms used from list"""
        self.platforms_used = json.dumps(platforms_list)

    def add_platform_used(self, platform):
        """Add a platform to the used platforms list"""
        platforms = self.get_platforms_used()
        if platform not in platforms:
            platforms.append(platform)
            self.set_platforms_used(platforms)

    def get_hashtags(self):
        """Get hashtags as list"""
        if self.hashtags:
            try:
                return json.loads(self.hashtags)
            except:
                return []
        return []

    def set_hashtags(self, hashtags_list):
        """Set hashtags from list"""
        self.hashtags = json.dumps(hashtags_list)

    def get_mentions(self):
        """Get mentions as list"""
        if self.mentions:
            try:
                return json.loads(self.mentions)
            except:
                return []
        return []

    def set_mentions(self, mentions_list):
        """Set mentions from list"""
        self.mentions = json.dumps(mentions_list)

    def get_performance_metrics(self):
        """Get performance metrics as dictionary"""
        if self.performance_metrics:
            try:
                return json.loads(self.performance_metrics)
            except:
                return {}
        return {}

    def set_performance_metrics(self, metrics_dict):
        """Set performance metrics from dictionary"""
        self.performance_metrics = json.dumps(metrics_dict)

    def update_performance_metric(self, metric_name, value):
        """Update a specific performance metric"""
        metrics = self.get_performance_metrics()
        metrics[metric_name] = value
        metrics['last_updated'] = datetime.utcnow().isoformat()
        self.set_performance_metrics(metrics)

    def increment_usage(self):
        """Increment usage count and update last used timestamp"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()

    def approve_content(self):
        """Approve the content for use"""
        self.status = 'approved'

    def reject_content(self, reason=None):
        """Reject the content"""
        self.status = 'rejected'
        if reason:
            metadata = self.get_metadata()
            metadata['rejection_reason'] = reason
            self.set_metadata(metadata)

    def publish_content(self, platform=None):
        """Mark content as published"""
        self.status = 'published'
        if platform:
            self.add_platform_used(platform)
        self.increment_usage()

    def get_file_url(self):
        """Get file URL if file exists"""
        if self.file_path and os.path.exists(self.file_path):
            # In production, this would return a proper URL
            return f"/api/content/{self.id}/file"
        return None

    def delete_file(self):
        """Delete associated file"""
        if self.file_path and os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
                return True
            except:
                return False
        return True

    def is_text_content(self):
        """Check if content is text-based"""
        return self.content_type in ['text', 'post', 'caption', 'description']

    def is_media_content(self):
        """Check if content is media-based"""
        return self.content_type in ['image', 'video', 'audio']

    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['metadata'] = self.get_metadata()
        data['generation_parameters'] = self.get_generation_parameters()
        data['platforms_used'] = self.get_platforms_used()
        data['hashtags'] = self.get_hashtags()
        data['mentions'] = self.get_mentions()
        data['performance_metrics'] = self.get_performance_metrics()
        data['file_url'] = self.get_file_url()
        data['is_text_content'] = self.is_text_content()
        data['is_media_content'] = self.is_media_content()
        return data

    @classmethod
    def get_user_content(cls, user_id, content_type=None, status=None, limit=50, offset=0):
        """Get user's content, optionally filtered by type and status"""
        query = cls.query.filter_by(user_id=user_id)

        if content_type:
            query = query.filter_by(content_type=content_type)

        if status:
            query = query.filter_by(status=status)

        return query.order_by(cls.created_at.desc())\
                   .limit(limit).offset(offset).all()

    @classmethod
    def get_campaign_content(cls, campaign_id, content_type=None):
        """Get content for a specific campaign"""
        query = cls.query.filter_by(campaign_id=campaign_id)

        if content_type:
            query = query.filter_by(content_type=content_type)

        return query.order_by(cls.created_at.desc()).all()

    @classmethod
    def get_top_performing_content(cls, user_id=None, limit=10):
        """Get top performing content based on usage and metrics"""
        query = cls.query.filter_by(status='published')

        if user_id:
            query = query.filter_by(user_id=user_id)

        return query.order_by(cls.usage_count.desc(), cls.quality_score.desc())\
                   .limit(limit).all()

    def __repr__(self):
        return f'<Content {self.title} - {self.content_type}>'


class ContentTemplate(BaseModel):
    """Content templates for consistent content generation"""
    __tablename__ = 'content_templates'

    # Template Details
    name = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    description_ar = db.Column(db.Text, nullable=True)

    # Template Type
    template_type = db.Column(db.String(50), nullable=False)  # post, story, ad, email, etc.
    content_type = db.Column(db.String(50), nullable=False)  # text, image, video, mixed

    # Template Content
    template_content = db.Column(db.Text, nullable=False)  # Template with placeholders

    # Template Parameters (JSON)
    parameters = db.Column(db.Text, nullable=True)  # JSON with parameter definitions

    # Usage & Performance
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    average_performance = db.Column(db.Float, default=0.0, nullable=False)

    # Template Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_premium = db.Column(db.Boolean, default=False, nullable=False)

    # Category & Tags
    category = db.Column(db.String(50), nullable=True)
    tags = db.Column(db.Text, nullable=True)  # JSON array of tags

    def get_parameters(self):
        """Get parameters as dictionary"""
        if self.parameters:
            try:
                return json.loads(self.parameters)
            except:
                return {}
        return {}

    def set_parameters(self, params_dict):
        """Set parameters from dictionary"""
        self.parameters = json.dumps(params_dict)

    def get_tags(self):
        """Get tags as list"""
        if self.tags:
            try:
                return json.loads(self.tags)
            except:
                return []
        return []

    def set_tags(self, tags_list):
        """Set tags from list"""
        self.tags = json.dumps(tags_list)

    def render_template(self, **kwargs):
        """Render template with provided parameters"""
        content = self.template_content

        # Simple placeholder replacement
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            content = content.replace(placeholder, str(value))

        return content

    def increment_usage(self, performance_score=None):
        """Increment usage count and update average performance"""
        self.usage_count += 1

        if performance_score is not None:
            # Update average performance
            total_score = self.average_performance * (self.usage_count - 1) + performance_score
            self.average_performance = total_score / self.usage_count

    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['parameters'] = self.get_parameters()
        data['tags'] = self.get_tags()
        return data

    @classmethod
    def get_active_templates(cls, template_type=None, category=None):
        """Get active templates, optionally filtered by type and category"""
        query = cls.query.filter_by(is_active=True)

        if template_type:
            query = query.filter_by(template_type=template_type)

        if category:
            query = query.filter_by(category=category)

        return query.order_by(cls.average_performance.desc(), cls.usage_count.desc()).all()

    @classmethod
    def get_popular_templates(cls, limit=10):
        """Get most popular templates"""
        return cls.query.filter_by(is_active=True)\
                       .order_by(cls.usage_count.desc())\
                       .limit(limit).all()

    def __repr__(self):
        return f'<ContentTemplate {self.name} - {self.template_type}>'