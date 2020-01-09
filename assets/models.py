from django.db import models

# Create your models here.
from django.contrib.auth.models import User
""" 导入 django.contrib.auto.models 内置的 User 表，作为我们 CMDB 项目的用户表，用于保存管理员和批准人员的信息；"""


class Asset(models.Model):
    """ 所有资产的共有数据表 
    sn 这个数据字段是所有资产都必须有，并且唯一不可重复的！通常来自自动收集的数据中；
    name 和 sn 一样，也是唯一的；
    asset_type_choice 和 asset_status 分别设计为两个选择类型
    adamin 和 approved_by 是分别是当前资产的管理员和将该资产上线的审批员，为了区分他们，设置了 related_name；
    Asset 表中的很多字段内容都无法自动获取，需要我们手动输入，比如合同、备注。
    最关键的是其中的一些外键字段，设置为on_delete=models.SET_NULL，这样的话，当关联的对象被删除的时候，不会影响到资产数据表。
    """

    assert_type_choice = (
        ('server', '服务器'),
        ('networddevice', '网络设备'),
        ('storagedevice', '存储设备'),
        ('securitydevice', '安全设备''),
        ('software', '软件资产''),
    )

    asset_status = (
        (0, '在线'),
        (1, '下线'),
        (2, '未知'),
        (3, '故障'),
        (4, '备用'),
    )
    assert_type = models.CharField(
        choices=assert_type_choice, max_length=64, default='server', verbose_name='资产类型')
    # unique=True时，在整个数据表内该字段的数据不可重复
    name = models.CharField(max_length=64, unique=True, verbose_name='资产名称')
    sn = models.CharField(max_length=128, unique=True, verbose_name='资产序列号')
    # 将外键字段设为null
    business_unit = models.ForeignKey(
        'BusinessUnit', null=True, blank=True, verbose_name='所属业务线', on_delete=models.SET_NULL)
    status = models.SmallIntegerField(
        choices=asset_status, default=0, verbose_name='设备状态')
    manufacturer = models.ForeignKey(
        'ManuFacturer', null=True, blank=True, verbose_name='制造商')
    manage_ip = models.GenericIPAddressField(
        null=True, blank=True, verbose_name='管理IP')
    tags = models.ManyToManyField('Tag', blank=True, verbose_name='标签')
    # related_name 用于关联对象反向引用模型的名称
    admin = models.ForeignKey(User, null=True, blank=True, verbose_name='资产管理员',
                              related_name='admin', on_delete=models.SET_NULL)
    idc = models.ForeignKey('IDC', null=True, blank=True,
                            verbose_name='所在机房', on_delete=models.SET_NULL)
    contract = models.ForeignKey(
        'Contract', null=True, blank=True, verbose_name='合同', on_delete=models.SET_NULL)

    purchase_day = models.DateField(null=True, blank=True, verbose_name='购买日期')
    expire_day = models.DateField(null=True, blank=True, verbose_name='过保日期')
    price = models.FloatField(null=True, blank=True, verbose_name='购买价格')

    approved_by = models.ForeignKey(User, null=True, blank=True, verbose_name='批准人',
                                    related_name='approved_by', on_delete=models.SET_NULL)

    memo = models.TextField(null=True, blank=True, verbose_name='备注')
    c_time = models.DateTimeField(auto_now_add=True, verbose_name='批准日期')
    m_time = models.DateTimeField(auto_now=True, verbose_name='更新日期')

    # 当print输出实例对象或str() 实例对象时，调用这个方法
    def __str__(self):
        return '<%s> %s' % (self.get_asset_type_display(), self.name)

    class Meta:
        verbose_name = '资产总表'  # 设置模型对象的直观、人类可读的名称
        verbose_name_plural = verbose_name
        ordering = ['-c_time']  # 指定该模型生成的所有对象的排序方式
