from rest_framework import serializers
from . import models
from rest_framework.exceptions import ValidationError
from flowback.decidables.fields import DecidableTypeChoices


class DecidableStumpSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()

    def get_attachments(self,obj):
        return AttachmentDetailSerializer(instance=obj.attachments,many=True).data

    class Meta:
        model = models.Decidable
        fields = "__all__"


class BreadCrumbDecidableSerializer(serializers.ModelSerializer):
    bread_crumb = serializers.SerializerMethodField()
    decidable_object = serializers.SerializerMethodField()

    def get_decidable_object(self,obj):
        return 'decidable'

    def get_bread_crumb(self,obj):
        if obj.primary_decidable:
            return BreadCrumbDecidableSerializer(instance=obj.primary_decidable).data
        if obj.parent_decidable:
            return BreadCrumbDecidableSerializer(instance=obj.parent_decidable).data
        if obj.parent_option:
            return BreadCrumbOptionSerializer(instance=obj.parent_option).data
        

    class Meta:
        model = models.Decidable
        fields = "__all__"


class BreadCrumbOptionSerializer(serializers.ModelSerializer):
    bread_crumb = serializers.SerializerMethodField()
    decidable_object = serializers.SerializerMethodField()

    def get_decidable_object(self,obj):
        return 'option'

    def get_bread_crumb(self,obj):
        decidable = obj.decidables.filter(primary_decidable__isnull=True).first()   
        return BreadCrumbDecidableSerializer(instance=decidable).data
        

    class Meta:
        model = models.Option
        fields = "__all__"


# Detail Serializers
class DecidableDetailSerializer(serializers.ModelSerializer):
    available_actions = serializers.SerializerMethodField()
    poll_rank = serializers.IntegerField(read_only=True)
    votes = serializers.IntegerField(read_only=True)
    user_vote = serializers.IntegerField(read_only=True)
    option_count = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
    root_state = serializers.SerializerMethodField()
    feed_channel = serializers.SerializerMethodField()
    linkfile_poll = serializers.SerializerMethodField()
    bread_crumb = serializers.SerializerMethodField()
    total_poll_count = serializers.IntegerField(read_only=True)

    def get_linkfile_poll(self,obj):
        linkfile_poll = obj.child_decidables.filter(
            decidable_type = DecidableTypeChoices.LINKFILEPOLL
        ).first()
        if not linkfile_poll:
            return
        return linkfile_poll.id
        

    def get_bread_crumb(self,obj):
        if obj.primary_decidable:
            return BreadCrumbDecidableSerializer(instance=obj.primary_decidable).data
        if obj.parent_decidable:
            return BreadCrumbDecidableSerializer(instance=obj.parent_decidable).data
        if obj.parent_option:
            return BreadCrumbOptionSerializer(instance=obj.parent_option).data
        

    def get_feed_channel(self,obj):
        from feed.serializers import ChannelSerializer
        return ChannelSerializer(instance=obj.feed_channel).data if hasattr(obj,'feed_channel') else None

    def get_root_state(self,obj):
        return obj.get_root_decidable().state

    def get_options(self,obj):
        return OptionListSerializer(instance=obj.options,many=True).data

    def get_attachments(self,obj):
        return AttachmentDetailSerializer(instance=obj.attachments,many=True).data


    def get_option_count(self,obj):
        return obj.options.count()
    
    def get_available_actions(self,obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return []
        return obj.fsm.get_available_actions(
            user=request.user
        )

    class Meta:
        model = models.Decidable
        fields = "__all__"



class OptionDetailSerializer(serializers.ModelSerializer):
    votes = serializers.IntegerField(read_only=True)
    user_vote = serializers.IntegerField(read_only=True)
    option_rank = serializers.IntegerField(read_only=True)
    total_option_count = serializers.IntegerField(read_only=True)
    attachments = serializers.SerializerMethodField()
    root_state = serializers.SerializerMethodField()
    reason_poll = serializers.SerializerMethodField()
    linkfile_poll = serializers.SerializerMethodField()
    bread_crumb = serializers.SerializerMethodField()
    feed_channel = serializers.SerializerMethodField()
    quorum = serializers.IntegerField(read_only=True)
    approval = serializers.IntegerField(read_only=True)

    def get_feed_channel(self,obj):
        from feed.serializers import ChannelSerializer
        return ChannelSerializer(instance=obj.feed_channel).data if hasattr(obj,'feed_channel') else None

    def get_bread_crumb(self,obj):
        decidable = obj.decidables.filter(primary_decidable__isnull=True).first()
        return BreadCrumbDecidableSerializer(instance=decidable).data

    def get_linkfile_poll(self,obj):
        linkfile_poll = obj.child_decidables.filter(
            decidable_type=DecidableTypeChoices.LINKFILEPOLL
        ).first()
        return DecidableStumpSerializer(instance=linkfile_poll).data

    def get_reason_poll(self,obj):
        reason_poll = obj.child_decidables.filter(
            decidable_type=DecidableTypeChoices.REASONPOLL
        ).first()
        return DecidableStumpSerializer(instance=reason_poll).data

    def get_root_state(self,obj):
        return obj.root_decidable.state

    
    class Meta:
        model = models.Option
        fields = "__all__"

    def get_attachments(self,obj):
        return AttachmentDetailSerializer(instance=obj.attachments,many=True).data


class AttachmentDetailSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)

    def get_name(self,obj):
        return obj.file.name if obj.file else obj.image.name if obj.image else ''
    
    def validate(self, attrs):
        attrs = super().validate(attrs)
        if sum([bool(attrs.get('link')),bool(attrs.get('file')),bool(attrs.get('image'))])>1:
            raise ValidationError('Multiple types sent at the same time')
        
        if attrs.get('type') == 'link' and not attrs.get('link'):
            raise ValidationError('Missing link')
        
        if attrs.get('type') == 'file' and not attrs.get('file'):
            raise ValidationError('Missing file')
        
        if attrs.get('type') == 'image' and not attrs.get('image'):
            raise ValidationError('Missing image')
        return attrs

    class Meta:
        model = models.Attachment
        fields = "__all__"


# List Serializers
class DecidableListSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()
    available_actions = serializers.SerializerMethodField()
    poll_rank = serializers.IntegerField(read_only=True)
    votes = serializers.IntegerField(read_only=True)
    user_vote = serializers.IntegerField(read_only=True)
    option_count = serializers.SerializerMethodField()
    root_state = serializers.SerializerMethodField()
    channel_feed = serializers.SerializerMethodField()
    total_poll_count = serializers.IntegerField(read_only=True)

    def get_channel_feed(self,obj):
        return obj.channel_feed if hasattr(obj,'channel_feed') else None

    def get_root_state(self,obj):
        return obj.get_root_decidable().state
    
    def get_option_count(self,obj):
        return obj.options.count()

    def get_rank(self,obj):
        return getattr(obj,'rank',None)

    def get_available_actions(self,obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return []
        return obj.fsm.get_available_actions(
            user=request.user
        )
    
    def get_attachments(self,obj):
        return AttachmentDetailSerializer(instance=obj.attachments,many=True).data

    
    class Meta:
        model = models.Decidable
        fields = "__all__"


class OptionListSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()
    votes = serializers.IntegerField(read_only=True)
    user_vote = serializers.IntegerField(read_only=True)
    option_rank = serializers.IntegerField(read_only=True)
    total_option_count = serializers.IntegerField(read_only=True)
    root_state = serializers.SerializerMethodField()
    reason_decidable = DecidableStumpSerializer(read_only=True)
    tags = serializers.SerializerMethodField()
    quorum = serializers.IntegerField(read_only=True)
    approval = serializers.IntegerField(read_only=True)

    def get_tags(self,obj):
        decidable = self.context.get('decidable')
        if not decidable:
            return
        
        decidable_option = obj.decidable_option.filter(
            decidable=decidable
        ).first()
        return decidable_option.tags

    def get_root_state(self,obj):
        return obj.root_decidable.state
    
    def get_attachments(self,obj):
        return AttachmentDetailSerializer(instance=obj.attachments,many=True).data

    class Meta:
        model = models.Option
        fields = "__all__"


# Create Serializers
class DecidableCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
    root_state = serializers.SerializerMethodField()

    def get_root_state(self,obj):
        return obj.get_root_decidable().state

    def get_options(self,obj):
        return OptionListSerializer(instance=obj.options,many=True).data

    def get_attachments(self,obj):
        return AttachmentDetailSerializer(instance=obj.attachments,many=True).data


    class Meta:
        model = models.Decidable
        fields = "__all__"


class OptionCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()
    root_state = serializers.SerializerMethodField()

    def get_root_state(self,obj):
        return obj.root_decidable.state
    
    def get_attachments(self,obj):
        return AttachmentDetailSerializer(instance=obj.attachments,many=True).data


    class Meta:
        model = models.Option
        fields = "__all__"
    
    def validate_tags(self,value):
        if not self.context.get('decidable'):
            return value
        decidable = self.context.get('decidable')

        # If decidable does not have tags but option has tags, raise error
        if not decidable.has_tags_flag and value:
            raise ValidationError('Should not have tag')

        # If decidable has tags and option's tags don't match, raise error
        if (
            decidable.has_tags_flag 
            and
            decidable.tags
        ):
            for tag in value:
                if tag not in decidable.tags:
                    raise ValidationError(f'"{tag}" does not exist in decidable tags')
        return value
    

class AttachmentCreateSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)

    def get_name(self,obj):
        return obj.file.name if obj.file else obj.image.name if obj.image else ''
    
    def validate(self, attrs):
        attrs = super().validate(attrs)
        if sum([bool(attrs.get('link')),bool(attrs.get('file')),bool(attrs.get('image'))])>1:
            raise ValidationError('Multiple types sent at the same time')
        
        if attrs.get('type') == 'link' and not attrs.get('link'):
            raise ValidationError('Missing link')
        
        if attrs.get('type') == 'file' and not attrs.get('file'):
            raise ValidationError('Missing file')
        
        if attrs.get('type') == 'image' and not attrs.get('image'):
            raise ValidationError('Missing image')
        return attrs

    class Meta:
        model = models.Attachment
        fields = "__all__"

