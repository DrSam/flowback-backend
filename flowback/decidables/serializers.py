from rest_framework import serializers
from . import models
from rest_framework.exceptions import ValidationError



class DecidableStumpSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Decidable
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
    attachments = serializers.SerializerMethodField()
    root_state = serializers.SerializerMethodField()
    reason_decidable = DecidableStumpSerializer(read_only=True)

    def get_root_state(self,obj):
        return obj.root_decidable.state

    
    class Meta:
        model = models.Option
        fields = "__all__"

    def get_attachments(self,obj):
        return AttachmentDetailSerializer(instance=obj.attachments,many=True).data


class AttachmentDetailSerializer(serializers.ModelSerializer):
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
    root_state = serializers.SerializerMethodField()
    reason_decidable = DecidableStumpSerializer(read_only=True)

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

