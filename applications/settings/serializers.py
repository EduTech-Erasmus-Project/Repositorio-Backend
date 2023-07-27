from rest_framework import serializers
from applications.settings import models


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Email
        fields = "__all__"


class OptionRegisterEmailExtensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OptionRegisterEmailExtension
        fields = ("type_option","id")


class EmailDomainTeacherSerializer(serializers.ModelSerializer):
    option_register_email = OptionRegisterEmailExtensionSerializer()

    class Meta:
        model = models.EmailExtensionsTeacher
        fields = ("id","domain","is_active","option_register_email")


class EmailDomainTeacherCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EmailExtensionsTeacher
        fields = "__all__"


class EmailDomainExpertSerializer(serializers.ModelSerializer):
    option_register_email = OptionRegisterEmailExtensionSerializer()

    class Meta:
        model = models.EmailExtensionsExpert
        fields = ("id","domain", "is_active", "option_register_email")


class EmailDomainExpertCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EmailExtensionsExpert
        fields = "__all__"


class EmailDomainStudentSerializer(serializers.ModelSerializer):
    option_register_email = OptionRegisterEmailExtensionSerializer()

    class Meta:
        model = models.EmailExtensionsStudent
        fields = ("id", "domain", "is_active", "option_register_email")


class EmailDomainStudentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.EmailExtensionsStudent
        fields = "__all__"


class UserTypeWithOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserTypeWithOption
        fields = "__all__"


class UserTypeWithOptionSerializerList(serializers.ModelSerializer):
    option_register = OptionRegisterEmailExtensionSerializer()

    class Meta:
        model = models.UserTypeWithOption
        fields = ("id", "description", "option_register")


