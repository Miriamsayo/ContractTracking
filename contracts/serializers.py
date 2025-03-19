from rest_framework import serializers
from .models import Contract

class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ["supervisor_approval", "hr_approval"]

    def update(self, instance, validated_data):
        user = self.context["request"].user

        # Supervisor approval logic
        if "supervisor_approval" in validated_data:
            if not user.is_superuser and user.role != "Admin" and user != instance.supervisor:
                raise serializers.ValidationError("Only the supervisor can approve.")
            instance.supervisor_approval = validated_data["supervisor_approval"]

        # HR approval logic
        if "hr_approval" in validated_data:
            if not instance.supervisor_approval:
                raise serializers.ValidationError("Supervisor approval is required first.")
            if user.role != "Admin":
                raise serializers.ValidationError("Only HR/Admin can approve.")
            instance.hr_approval = validated_data["hr_approval"]

        instance.save()
        return instance
