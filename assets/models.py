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

    asset_type_choice = (
        ('server', '服务器'),
        ('networddevice', '网络设备'),
        ('storagedevice', '存储设备'),
        ('securitydevice', '安全设备'),
        ('software', '软件资产'),
    )

    asset_status = (
        (0, '在线'),
        (1, '下线'),
        (2, '未知'),
        (3, '故障'),
        (4, '备用'),
    )
    asset_type = models.CharField(choices=asset_type_choice,
                                  max_length=64,
                                  default='server',
                                  verbose_name='资产类型')
    # unique=True时，在整个数据表内该字段的数据不可重复
    name = models.CharField(max_length=64, unique=True, verbose_name='资产名称')
    sn = models.CharField(max_length=128, unique=True, verbose_name='资产序列号')
    # 将外键字段设为null
    business_unit = models.ForeignKey('BusinessUnit',
                                      null=True,
                                      blank=True,
                                      verbose_name='所属业务线',
                                      on_delete=models.SET_NULL)
    status = models.SmallIntegerField(choices=asset_status,
                                      default=0,
                                      verbose_name='设备状态')
    manufacturer = models.ForeignKey('ManuFacturer',
                                     null=True,
                                     blank=True,
                                     verbose_name='制造商',
                                     on_delete=models.SET_NULL)
    manage_ip = models.GenericIPAddressField(null=True,
                                             blank=True,
                                             verbose_name='管理IP')
    tags = models.ManyToManyField('Tag', blank=True, verbose_name='标签')
    # related_name 用于关联对象反向引用模型的名称
    admin = models.ForeignKey(User,
                              null=True,
                              blank=True,
                              verbose_name='资产管理员',
                              related_name='admin',
                              on_delete=models.SET_NULL)
    idc = models.ForeignKey('IDC',
                            null=True,
                            blank=True,
                            verbose_name='所在机房',
                            on_delete=models.SET_NULL)
    contract = models.ForeignKey('Contract',
                                 null=True,
                                 blank=True,
                                 verbose_name='合同',
                                 on_delete=models.SET_NULL)

    purchase_day = models.DateField(null=True, blank=True, verbose_name='购买日期')
    expire_day = models.DateField(null=True, blank=True, verbose_name='过保日期')
    price = models.FloatField(null=True, blank=True, verbose_name='购买价格')

    approved_by = models.ForeignKey(User,
                                    null=True,
                                    blank=True,
                                    verbose_name='批准人',
                                    related_name='approved_by',
                                    on_delete=models.SET_NULL)

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


class Server(models.Model):
    """ 服务器设备
    每台服务器都唯一关联着一个资产对象，因此使用 OneToOneField 构建了一个一对一字段，这非常重要!
    服务器又可分为几种子类型，这里定义了三种；
    服务器添加的方式可以分为手动和自动；
    有些服务器是虚拟机或者 docker 生成的，没有物理实体，存在于宿主机中，因此需要增加一个 hosted_on 字段；这里认为，宿主机如果被删除，虚拟机也就不存在了；
    服务器有型号信息，如果硬件信息中不包含，那么指的就是主板型号；
    Raid 类型在采用了 Raid 的时候才有，否则为空
    操作系统相关信息包含类型、发行版本和具体版本
    """

    sub_asset_type_choice = (
        (0, 'PC服务器'),
        (1, '刀片机'),
        (2, '小型机'),
    )
    created_by_choice = (
        ('auto', '自动添加'),
        ('manual', '手工添加'),
    )

    # 非常关键的一对一关联！asset被删除的时候一并删除server
    asset = models.OneToOneField('Asset', on_delete=models.CASCADE)
    sub_asset_type = models.SmallIntegerField(choices=sub_asset_type_choice,
                                              default=0,
                                              verbose_name='服务器类型')
    created_by = models.CharField(choices=created_by_choice,
                                  max_length=32,
                                  default='auto',
                                  verbose_name='添加方式')
    hosted_on = models.ForeignKey('self',
                                  related_name='hosted_on_server',
                                  blank=True,
                                  null=True,
                                  verbose_name='宿主机',
                                  on_delete=models.CASCADE)  # 虚拟机专用字段
    model = models.CharField(max_length=128,
                             null=True,
                             blank=True,
                             verbose_name='服务器型号')
    raid_type = models.CharField(max_length=512,
                                 null=True,
                                 blank=True,
                                 verbose_name='Raid类型')

    os_type = models.CharField(max_length=64,
                               null=True,
                               blank=True,
                               verbose_name='操作系统类型')
    os_distribution = models.CharField(max_length=64,
                                       null=True,
                                       blank=True,
                                       verbose_name='发行商')
    os_release = models.CharField(max_length=64,
                                  null=True,
                                  blank=True,
                                  verbose_name='操作系统版本')

    def __str__(self):
        return '%s--%s--%s <sn:%s>' % (self.asset.name,
                                       self.get_sub_asset_type_dispaly(),
                                       self.model, self.asset.sn)

    class Meta:
        verbose_name = '服务器'
        verbose_name_plural = verbose_name


class SecurityDevice(models.Model):
    """ 安全设备 """

    sub_asset_type_choice = (
        (0, '防火墙'),
        (1, '入侵检测设备'),
        (2, '互联网网关'),
        (4, '运维审计系统'),
    )
    asset = models.OneToOneField('Asset', on_delete=models.CASCADE)
    sub_asset_type = models.SmallIntegerField(choices=sub_asset_type_choice,
                                              default=0,
                                              verbose_name='安全设备类型')
    model = models.CharField(max_length=128,
                             default='未知型号',
                             verbose_name='安全设备型号')

    def __str__(self):
        return self.asset.name + '--' + self.get_sub_asset_type_dispaly(
        ) + str(self.model) + " id:%s " % self.id

    class Meta:
        verbose_name = '安全设备'
        verbose_name_plural = verbose_name


class StorageDevice(models.Model):
    """ 存储设备 """
    sub_asset_type_choice = (
        (0, '磁盘阵列'),
        (1, '网络存储器'),
        (2, '磁带库'),
        (4, '磁带机'),
    )

    asset = models.OneToOneField('Asset', on_delete=models.CASCADE)
    sub_asset_type = models.SmallIntegerField(choices=sub_asset_type_choice,
                                              default=0,
                                              verbose_name='存储设备类型')
    model = models.CharField(max_length=128,
                             default='未知型号',
                             verbose_name='存储设备型号')

    def __str__(self):
        return self.asset.name + '--' + self.get_sub_asset_type_dispaly(
        ) + str(self.model) + 'id:%s' % self.id

    class Meta:
        verbose_name = '存储设备'
        verbose_name_plural = verbose_name


class NetworkDevice(models.Model):
    """ 网络设备 """
    sub_asset_type_choice = (
        (0, '路由器'),
        (1, '交换机'),
        (2, '负载均衡'),
        (4, 'VPN设备'),
    )

    asset = models.OneToOneField('Asset', on_delete=models.CASCADE)
    sub_asset_type = models.SmallIntegerField(choices=sub_asset_type_choice,
                                              default=0,
                                              verbose_name='网络设备类型')
    model = models.CharField(max_length=128,
                             default='未知型号',
                             verbose_name='网络设备型号')

    vlan_ip = models.GenericIPAddressField(blank=True,
                                           null=True,
                                           verbose_name='VlanIP')
    intranet_ip = models.GenericIPAddressField(blank=True,
                                               null=True,
                                               verbose_name='内网IP')

    firmware = models.CharField(max_length=128,
                                blank=True,
                                null=True,
                                verbose_name='设备固件版本')
    port_num = models.SmallIntegerField(null=True,
                                        blank=True,
                                        verbose_name='端口个数')
    device_detail = models.TextField(null=True,
                                     blank=True,
                                     verbose_name='详细配置')

    def __str__(self):
        return '%s--%s--%s <sn:%s>' % (self.asset.name,
                                       self.get_sub_asset_type_dispaly(),
                                       self.modelm, self.asset.sn)

    class Meta:
        verbose_name = '网络设备'
        verbose_name_plural = verbose_name


class Software(models.Model):
    """ 只保存付费购买的软件
    对于软件，它没有物理形体，因此无须关联一个资产对象；
    软件只管理那些大型的收费软件，关注点是授权数量和软件版本。对于那些开源的或者免费的软件，显然不算公司的资产
    """
    sub_asset_type_choice = (
        (0, '操作系统'),
        (1, '办公/开发软件'),
        (2, '业务软件'),
    )

    sub_asset_type = models.SmallIntegerField(choices=sub_asset_type_choice,
                                              default=0,
                                              verbose_name='网络设备类型')
    license_num = models.IntegerField(default=1, verbose_name='授权数量')
    version = models.CharField(max_length=64,
                               unique=True,
                               help_text='例如: RedHat relate 7 (Final)',
                               verbose_name='软件/系统版本')

    def __str__(self):
        return '%s--%s' % (self.get_sub_asset_type_dispaly(), self.version())

    class Meta:
        verbose_name = '软件/系统'
        verbose_name_plural = verbose_name


class CPU(models.Model):
    """ CPU组件 """
    asset = models.OneToOneField('Asset', on_delete=models.CASCADE)
    cpu_model = models.CharField(max_length=128, verbose_name='CPU型号')
    # 正整数字段，包含0,最大2147483647。
    cpu_count = models.PositiveIntegerField(default=1, verbose_name='物理CPU个数')
    # 较小的正整数字段，从0到32767
    cpu_core_count = models.PositiveSmallIntegerField(default=1,
                                                      verbose_name='CPU核数')
    cpu_thread_count = models.PositiveSmallIntegerField(default=1,
                                                        verbose_name='CPU线程数')
    cpu_frequency = models.DecimalField(max_digits=3,
                                        decimal_places=2,
                                        verbose_name='CPU主频(GHZ)')

    def __str__(self):
        return '%s: %s' % (self.asset.name, self.cpu.model)

    class Meta:
        verbose_name = 'CPU'
        verbose_name_plural = verbose_name


class RAM(models.Model):
    """ 内存组件 """
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)
    sn = models.CharField('SN号', max_length=128, blank=True, null=True)
    model = models.CharField('内存型号', max_length=128, blank=True, null=True)
    manufacturer = models.CharField('内存制造商',
                                    max_length=128,
                                    blank=True,
                                    null=True)
    slot = models.CharField('插槽', max_length=64)
    capacity = models.IntegerField('内存大小(GB)', blank=True, null=True)
    frequency = models.IntegerField('内存频率(MHZ)', blank=True, null=True)

    def __str__(self):
        return '%s: %s :%s :%s :%s' % (self.asset.name, self.model, self.slot,
                                       self.capacity, self.ram_frequency)

    class Meta:
        verbose_name = '内存'
        verbose_name_plural = verbose_name
        # 联合主键约束
        unique_together = ('asset', 'slot')  # 同一资产下的内存，根据插槽的不同，必须唯一


class Disk(models.Model):
    """ 存储设备 """
    disk_interface_type_choice = (
        ('SATA', 'SATA'),
        ('SAS', 'SAS'),
        ('SCSI', 'SCSI'),
        ('M.2', 'M.2'),
        ('unknown', 'unknown'),
    )

    disk_protocol_choice = (
        ('SATA', 'SATA'),
        ('NVME', 'NVME'),
        ('unknown', 'unknown'),
    )

    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)
    sn = models.CharField('硬盘SN号', max_length=128)
    slot = models.CharField('所在插槽位', max_length=64, blank=True, null=True)
    model = models.CharField('磁盘型号', max_length=64, blank=True, null=True)
    manufacturer = models.CharField('磁盘制造商',
                                    max_length=64,
                                    blank=True,
                                    null=True)
    capacity = models.FloatField('磁盘容量(GB)', blank=True, null=True)
    interface_type = models.CharField('接口类型',
                                      max_length=16,
                                      choices=disk_interface_type_choice,
                                      default='unknown')
    disk_protocol = models.CharField('磁盘协议',
                                     max_length=16,
                                     choices=disk_protocol_choice,
                                     default='SATA')

    def __str__(self):
        return '%s: %s: %s: %sGB: %s ' % (self.asset.name, self.model,
                                          self.slot, self.capacity)

    class Meta:
        verbose_name = '硬盘'
        verbose_name_plural = verbose_name
        unique_together = ('asset', 'sn')


class NIC(models.Model):
    """
    网卡组件
    一台设备中可能有很多块网卡，所以网卡与资产是外键的关系
    """
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)  # 外键
    name = models.CharField('网卡名称', max_length=64, blank=True, null=True)
    model = models.CharField('网卡型号', max_length=64)
    mac = models.CharField('MAC地址', max_length=64)
    id_address = models.GenericIPAddressField('IP地址', blank=True, null=True)
    net_mask = models.CharField('掩码', max_length=64, blank=True, null=True)
    bonding = models.CharField('绑定地址', max_length=64, blank=True, null=True)
    manufacturer = models.CharField('网卡制造商',
                                    max_length=64,
                                    blank=True,
                                    null=True)

    def __str__(self):
        return '%s: %s: %s: %s ' % (self.asset.name, self.model, self.mac)

    class Meta:
        verbose_name = '网卡'
        verbose_name_plural = verbose_name
        # 资产、型号和mac必须联合唯一。防止虚拟机中的特殊情况发生错误
        unique_together = ('asset', 'model', 'mac')


class IDC(models.Model):
    """ 机房
    机房可以有很多其它字段，比如城市、楼号、楼层和未知等等，如有需要可自行添加； """
    name = models.CharField(max_length=64, unique=True, verbose_name='机房名称')
    memo = models.CharField(max_length=128,
                            blank=True,
                            null=True,
                            verbose_name='备注')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '机房'
        verbose_name_plural = verbose_name


class Manufacturer(models.Model):
    """ 厂商 """
    name = models.CharField(max_length=64, unique=True, verbose_name='厂商名称')
    telephone = models.CharField(max_length=30,
                                 blank=True,
                                 null=True,
                                 verbose_name='支持电话')
    memo = models.CharField(max_length=128,
                            blank=True,
                            null=True,
                            verbose_name='备注')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '厂商'
        verbose_name_plural = verbose_name


class BusinessUnit(models.Model):
    """ 业务线
    业务线可以有子业务线，因此使用一个外键关联自身模型 """
    parent_unit = models.ForeignKey('self',
                                    blank=True,
                                    null=True,
                                    related_name='parent_level',
                                    on_delete=models.SET_NULL)
    telephone = models.CharField(max_length=30,
                                 blank=True,
                                 null=True,
                                 verbose_name='业务线')
    memo = models.CharField(max_length=128,
                            blank=True,
                            null=True,
                            verbose_name='备注')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '业务线'
        verbose_name_plural = verbose_name


class Contract(models.Model):
    """ 合同
    合同模型主要存储财务部门关心的数据； """
    sn = models.CharField(max_length=128, unique=True, verbose_name='合同号')
    name = models.CharField(max_length=64, verbose_name='合同名称')
    memo = models.TextField(blank=True, null=True, verbose_name='备注')
    price = models.DecimalField(max_digits=15,
                                decimal_places=2,
                                verbose_name='合同金额')
    detail = models.TextField(blank=True, null=True, verbose_name='合同详细')
    start_day = models.DateField(blank=True, null=True, verbose_name='开始日期')
    end_day = models.DateField(blank=True, null=True, verbose_name='失效日期')
    license_num = models.IntegerField(blank=True,
                                      null=True,
                                      verbose_name='license数量')
    c_day = models.DateField(auto_now_add=True, verbose_name='创建日期')
    m_day = models.DateField(auto_now=True, verbose_name='修改日期')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '合同'
        verbose_name_plural = verbose_name


class Tag(models.Model):
    """ 资产标签
    资产标签模型与资产是多对多的关系 """
    name = models.CharField(max_length=32, unique=True, verbose_name='标签名')
    c_day = models.DateField(auto_now_add=True, verbose_name='创建日期')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = verbose_name


class EventLog(models.Model):
    """ 日志 """

    event_type_choice = (
        (0, '其他'),
        (1, '硬件变更'),
        (2, '新增配件'),
        (3, '设备下线'),
        (4, '设备上线'),
        (5, '定期维护'),
        (6, '业务上线/更新/变更'),
    )
    name = models.CharField('事件名称', max_length=128)
    asset = models.ForeignKey('Asset',
                              blank=True,
                              null=True,
                              on_delete=models.SET_NULL)  # 当资产审批成功时有这项数据
    event_type = models.SmallIntegerField('时间类型',
                                          choices=event_type_choice,
                                          default=4)
    component = models.CharField('事件子项', max_length=256, blank=True, null=True)
    datail = models.TextField('事件详情')
    date = models.DateTimeField('事件时间', auto_now_add=True)
    user = models.ForeignKey(User,
                             blank=True,
                             null=True,
                             verbose_name='事件执行人',
                             on_delete=models.SET_NULL)
    memo = models.TextField('备注', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '事件记录'
        verbose_name_plural = verbose_name


class NewAssetApprovalZone(models.Model):
    """ 新资产待审批区 """
    asset_type_choice = (
        ('server', '服务器'),
        ('networkdevice', '网络设备'),
        ('storagedevice', '存储设备'),
        ('securitydevice', '安全设备'),
        ('software', '软件资产'),
    )
    sn = models.CharField('资产SN号', max_length=128, unique=True)
    asset_type = models.CharField(choices=asset_type_choice,
                                  default='server',
                                  max_length=64,
                                  blank=True,
                                  verbose_name='资产类型')
    manufacturer = models.CharField(max_length=64,
                                    blank=True,
                                    null=True,
                                    verbose_name='生产厂商')
    model = models.CharField(max_length=128,
                             blank=True,
                             null=True,
                             verbose_name='型号')
    ram_size = models.PositiveIntegerField(blank=True,
                                           null=True,
                                           verbose_name='内存大小')
    cpu_model = models.CharField(max_length=128,
                                 blank=True,
                                 null=True,
                                 verbose_name='CPU型号')
    cpu_count = models.PositiveSmallIntegerField(blank=True,
                                                 null=True,
                                                 verbose_name='CPU物理数量')
    cpu_core_count = models.PositiveSmallIntegerField(blank=True,
                                                      null=True,
                                                      verbose_name='CPU核心数量')
    os_distribution = models.CharField('发行商',
                                       max_length=64,
                                       blank=True,
                                       null=True)
    os_type = models.CharField('系统类型', max_length=64, blank=True, null=True)
    os_release = models.CharField('操作系统版本号',
                                  max_length=64,
                                  blank=True,
                                  null=True)

    data = models.TextField('资产数据')  # 此字段必填

    c_time = models.DateTimeField(auto_now_add=True, verbose_name='汇报日期')
    m_time = models.DateTimeField(auto_now=True, verbose_name='批准日期')
    approved = models.BooleanField('是否批准', default=False)

    def __str__(self):
        return self.sn

    class Meta:
        verbose_name = '新上线待审批资产'
        verbose_name_plural = verbose_name
        ordering = ['-c_time']
