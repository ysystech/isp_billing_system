
from apps.utils.models import BaseModel
from apps.customer_installations.models import CustomerInstallation
from apps.subscriptions.models import SubscriptionPlan


from django.db import models


class CustomerSubscription(BaseModel):
    SUBSCRIPTION_TYPES = [
        ('one_month', '1 Month'),
        ('fifteen_days', '15 Days'),
        ('custom', 'Custom')
    ]
    
    customer_installation = models.ForeignKey(CustomerInstallation, on_delete=models.PROTECT)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    subscription_type = models.CharField(max_length=255, choices=SUBSCRIPTION_TYPES)
    
    # Subscription details
    start_date = models.DateField()
    end_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    days_added = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=255)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.customer.full_name} - {self.subscription_type}"
    

    """
        The customer subscription is a prepaid style of subscription.
        The customer will pay for the subscription upfront and the subscription will be active for the duration of the subscription.

        Example if the price of a plan selected is 1000 (SubscriptionPlan model):
        - If the subscription type is 1 month, then the customer will pay 1000 (days added +1month)
        - If the subscription type is 15 days, then the customer will pay 500 (days added +15days)
        - If custom that means the cashier can input the custom amount like 200 then this will be the calculation:
            - Formula: (custom amount / price of plan) * 30 = days added
            - 200 / 1000 = 0.2 * 30 = 6 days
            - 100 / 1000 = 0.1 * 30 = 3 days
            - 150 / 1000 = 0.15 * 30 = 4.5 days
    """