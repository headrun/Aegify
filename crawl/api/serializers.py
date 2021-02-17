import os

from django.db.models import Q

from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.serializers import ListSerializer

from base.utils import get_media_path
from base.settings import DjangoUtil;
from base.serializers import *
settings = DjangoUtil.settings()

class BaseSourceSerializer(BaseModelSerializer):

    class Meta(BaseModelSerializer.Meta):
        fields = ['name', 'aka', 'url', 'fullname']
        read_only_fields = ['url', 'fullname']

class BaseItemKeySerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        fields = ['source', 'key', 'url']

class BaseItemDetailListSerializer(ListSerializer):
    def to_representation(self, *args, **kwargs):
        data_list = []
        for data in super().to_representation(*args, **kwargs):
            if not data.get('data', {}).get('http_status'):
                data_list.append(data)

        return data_list

class BaseItemDetailSerializer(BaseModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        fields = ['source', 'key', 'url', 'active', 'data']

        list_serializer_class = BaseItemDetailListSerializer

    def get_data(self, obj):
        data = {}
        for d in self.get_data_list(obj):
            if d.name is '':
                data.update(d.json)
            else:
                data.setdefault(d.name, []).append(d.json)
        return data

    def get_data_list(self, obj):
        data_params = getattr(self, 'data_params', {})
        if data_params:
            try:
                param_dict = {}
                for key, val in data_params.items():
                    if ':' not in key:
                         continue

                    try:
                        val = eval(val)
                    except:
                        pass
                    name, param = key.split(':', 1)

                    param = param.strip()
                    if not param:
                        continue
                    param_dict.setdefault(name, {})[param] = val

                if param_dict:
                    args = ~Q(name__in=param_dict.keys())
                    for name, params in param_dict.items():
                        args |= Q(name=name, **params)

                    objs = obj.data_list.filter(args)
                    list(objs)
                    return objs
            except Exception as e:
                e = obj.InvalidDataException()
                e.http_status = HTTP_400_BAD_REQUEST
                raise e

        return obj.data_list.all()

    def update_media_urls(self, urls):
        val = []
        for i, url in enumerate(urls):
            path = get_media_path(url)
            if url != path:
                url = DjangoUtil.get_absolute_url(self._context['request'], os.path.join(settings.MEDIA_URL, path))
            val.append(url)
        return val

class BaseItemListCreateSerializer(BaseItemDetailSerializer):
    active = serializers.BooleanField(default=True)

    def create(self, validated_data):
        self.modify_input(validated_data)
        return super().create(validated_data)

    def update(self, obj, validated_data):
        self.modify_input(validated_data)
        return super().update(obj, validated_data)

    def modify_input(self, validated_data):
        source_model = self.fields['source'].Meta.model
        source_name = validated_data.pop('source').get('name', '')
        if not source_name:
            raise source_model.DoesNotExist
        
        try:
            validated_data['source'] = source_model.objects.get(name=source_name)
            try:
                if source_model.objects.get(name=source_name).parent:
                    validated_data['source'] = source_model.objects.get(name=source_name).parent
            except:pass
        except:
            validated_data['source'] = source_model.objects.get(aka=source_name)
