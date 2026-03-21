from django import forms
from .models import AuctionSession
from items.models import AuctionItem

class AuctionSessionForm(forms.ModelForm):
    """
    自定义后台表单：将 item 字段改为多选
    """
    # 定义一个多选字段，替代原有的单选字段
    # queryset 限制为“待开拍”的商品，防止把已卖出的拿来卖
    items = forms.ModelMultipleChoiceField(
        queryset=AuctionItem.objects.filter(status__in=[1, 4]), # 1=待开拍, 4=流拍
        label="关联拍品 (支持多选)",
        help_text="按住 Ctrl (Win) 或 Command (Mac) 键可多选。保存后系统将自动为每个拍品创建独立的场次。",
        required=True
    )

    class Meta:
        model = AuctionSession
        fields = '__all__'
        exclude = ['item'] # 隐藏原本的单选字段，用上面的多选代替

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果是修改页面，回显当前关联的那个拍品
        if self.instance and self.instance.pk:
            self.fields['items'].initial = [self.instance.item]
            
        # 拍卖规则字段由商品本身决定，管理员无需必填
        for field in ['auction_type', 'price_step', 'reduce_interval', 'bottom_price']:
            if field in self.fields:
                self.fields[field].required = False