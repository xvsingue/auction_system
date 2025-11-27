from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    用户注册序列化器
    处理用户创建、密码加密及角色特定的字段校验
    """
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password', 'email', 'role', 'id_card', 'business_license']

    def validate(self, data):
        # 1. 密码一致性校验
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError("两次输入的密码不一致")

        # 2. 角色特定校验 (符合 3.1.1 注册与审核需求)
        role = data.get('role')
        if role == 'seller' and not data.get('business_license'):
            raise serializers.ValidationError({"business_license": "卖家注册必须上传营业执照"})

        # 3. 身份证简单校验 (毕设场景仅做长度校验)
        id_card = data.get('id_card')
        if id_card and len(id_card) != 18:
            raise serializers.ValidationError({"id_card": "身份证号码必须为18位"})

        return data

    def create(self, validated_data):
        # 移除确认密码，不存入数据库
        validated_data.pop('confirm_password')
        # 使用 create_user 方法自动处理密码加密
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    用户信息序列化器
    用于个人中心展示和修改
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'credit_rating', 'balance', 'date_joined', 'id_card',
                  'business_license']
        read_only_fields = ['id', 'username', 'role', 'credit_rating', 'balance', 'date_joined']  # 这些字段禁止前端直接修改