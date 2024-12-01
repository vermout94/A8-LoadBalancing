import pulumi
from pulumi_azure_native import compute, network, resources, authorization

# Configuration and Credentials
config = pulumi.Config()
admin_username = config.require('adminUsername')
admin_password = config.require_secret('adminPassword')

# Get Subscription ID
client_config = authorization.get_client_config()
subscription_id = client_config.subscription_id

# Create Resource Group with explicit name
resource_group = resources.ResourceGroup(
    'resourceGroup',
)

# Define Virtual Network and Subnet
vnet = network.VirtualNetwork(
    'vnet',
    resource_group_name=resource_group.name,
    location=resource_group.location,
    virtual_network_name='vnet',  # Set the Azure VNet name
    address_space=network.AddressSpaceArgs(
        address_prefixes=['10.0.0.0/16'],
    ),
)

subnet = network.Subnet(
    'subnet',
    resource_group_name=resource_group.name,
    virtual_network_name=vnet.name,
    subnet_name='subnet',  # Set the Azure Subnet name
    address_prefix='10.0.1.0/24',
)

# Define Public IP Address with explicit name
public_ip_name = 'publicIP'
public_ip = network.PublicIPAddress(
    'publicIP',
    public_ip_address_name=public_ip_name,  # Set the Azure Public IP name
    resource_group_name=resource_group.name,
    location=resource_group.location,
    sku=network.PublicIPAddressSkuArgs(
        name='Standard',
    ),
    public_ip_allocation_method='Static',
    public_ip_address_version='IPv4',
    zones=['1', '2', '3'],
)

# Define Load Balancer Name and Backend Pool Name
load_balancer_name = 'loadBalancer'
backend_pool_name = 'backendPool'

# Define Load Balancer with explicit name
load_balancer = network.LoadBalancer(
    'loadBalancer',
    load_balancer_name=load_balancer_name,  # Set the Azure Load Balancer name
    resource_group_name=resource_group.name,
    location=resource_group.location,
    sku=network.LoadBalancerSkuArgs(
        name='Standard',
    ),
    frontend_ip_configurations=[
        network.FrontendIPConfigurationArgs(
            name='loadBalancerFrontEnd',
            public_ip_address=network.PublicIPAddressArgs(
                id=public_ip.id,
            ),
        )
    ],
    backend_address_pools=[
        network.BackendAddressPoolArgs(
            name=backend_pool_name,
        )
    ],
    probes=[
        network.ProbeArgs(
            name='healthProbe',
            protocol='Http',
            port=80,
            request_path='/',
            interval_in_seconds=5,
            number_of_probes=2,
        )
    ],
    load_balancing_rules=[
        network.LoadBalancingRuleArgs(
            name='loadBalancingRule',
            protocol='Tcp',
            frontend_port=80,
            backend_port=80,
            frontend_ip_configuration=network.SubResourceArgs(
                id=pulumi.Output.all(subscription_id, resource_group.name).apply(
                    lambda args: f"/subscriptions/{args[0]}/resourceGroups/{args[1]}/providers/Microsoft.Network/loadBalancers/{load_balancer_name}/frontendIPConfigurations/loadBalancerFrontEnd"
                ),
            ),
            backend_address_pool=network.SubResourceArgs(
                id=pulumi.Output.all(subscription_id, resource_group.name).apply(
                    lambda args: f"/subscriptions/{args[0]}/resourceGroups/{args[1]}/providers/Microsoft.Network/loadBalancers/{load_balancer_name}/backendAddressPools/{backend_pool_name}"
                ),
            ),
            probe=network.SubResourceArgs(
                id=pulumi.Output.all(subscription_id, resource_group.name).apply(
                    lambda args: f"/subscriptions/{args[0]}/resourceGroups/{args[1]}/providers/Microsoft.Network/loadBalancers/{load_balancer_name}/probes/healthProbe"
                ),
            ),
        )
    ],
)

# Define Network Interfaces and Associate with Backend Pool
backend_address_pool_id = pulumi.Output.all(subscription_id, resource_group.name).apply(
    lambda args: f"/subscriptions/{args[0]}/resourceGroups/{args[1]}/providers/Microsoft.Network/loadBalancers/{load_balancer_name}/backendAddressPools/{backend_pool_name}"
)

nic1 = network.NetworkInterface(
    'nic1',
    network_interface_name='nic1',  # Set the Azure NIC name
    resource_group_name=resource_group.name,
    location=resource_group.location,
    ip_configurations=[
        network.NetworkInterfaceIPConfigurationArgs(
            name='ipconfig1',
            subnet=network.SubnetArgs(
                id=subnet.id,
            ),
            private_ip_allocation_method='Dynamic',
            load_balancer_backend_address_pools=[
                network.BackendAddressPoolArgs(
                    id=backend_address_pool_id,
                )
            ],
        )
    ],
)

nic2 = network.NetworkInterface(
    'nic2',
    network_interface_name='nic2',  # Set the Azure NIC name
    resource_group_name=resource_group.name,
    location=resource_group.location,
    ip_configurations=[
        network.NetworkInterfaceIPConfigurationArgs(
            name='ipconfig1',
            subnet=network.SubnetArgs(
                id=subnet.id,
            ),
            private_ip_allocation_method='Dynamic',
            load_balancer_backend_address_pools=[
                network.BackendAddressPoolArgs(
                    id=backend_address_pool_id,
                )
            ],
        )
    ],
)


# Create Virtual Machines with explicit names
vm1 = compute.VirtualMachine(
    'vm1',
    resource_group_name=resource_group.name,
    location=resource_group.location,
    hardware_profile=compute.HardwareProfileArgs(
        vm_size='Standard_B1ls',
    ),
    os_profile=compute.OSProfileArgs(
        computer_name='vm1',
        admin_username=admin_username,
        admin_password=admin_password,
    ),
    network_profile=compute.NetworkProfileArgs(
        network_interfaces=[
            compute.NetworkInterfaceReferenceArgs(
                id=nic1.id,
            )
        ],
    ),
    storage_profile=compute.StorageProfileArgs(
        os_disk=compute.OSDiskArgs(
            name='vm1_os_disk',
            create_option='FromImage',
        ),
        image_reference=compute.ImageReferenceArgs(
            publisher='Canonical',
            offer='UbuntuServer',
            sku='18.04-LTS',
            version='latest',
        ),
    ),
)

vm2 = compute.VirtualMachine(
    'vm2',
    resource_group_name=resource_group.name,
    location=resource_group.location,
    hardware_profile=compute.HardwareProfileArgs(
        vm_size='Standard_B1ls',
    ),
    os_profile=compute.OSProfileArgs(
        computer_name='vm2',
        admin_username=admin_username,
        admin_password=admin_password,
    ),
    network_profile=compute.NetworkProfileArgs(
        network_interfaces=[
            compute.NetworkInterfaceReferenceArgs(
                id=nic2.id,
            )
        ],
    ),
    storage_profile=compute.StorageProfileArgs(
        os_disk=compute.OSDiskArgs(
            name='vm2_os_disk',
            create_option='FromImage',
        ),
        image_reference=compute.ImageReferenceArgs(
            publisher='Canonical',
            offer='UbuntuServer',
            sku='18.04-LTS',
            version='latest',
        ),
    ),
)

vm1_extension = compute.VirtualMachineExtension("vm1Extension",
    resource_group_name=resource_group.name,
    vm_name=vm1.name,
    vm_extension_name="installNginx",
    publisher="Microsoft.Azure.Extensions",
    type="CustomScript",
    type_handler_version="2.1",
    auto_upgrade_minor_version=True,
    settings={
        "commandToExecute": "sudo apt-get update && "
                            "sudo apt-get install -y nginx && "
                            "echo 'Hello from VM1' | sudo tee /var/www/html/index.html"
                            "sudo systemctl restart nginx"
    })

vm2_extension = compute.VirtualMachineExtension("vm2Extension",
    resource_group_name=resource_group.name,
    vm_name=vm2.name,
    vm_extension_name="installNginx",
    publisher="Microsoft.Azure.Extensions",
    type="CustomScript",
    type_handler_version="2.1",
    auto_upgrade_minor_version=True,
    settings={
        "commandToExecute": "sudo apt-get update && "
                            "sudo apt-get install -y nginx && "
                            "echo 'Hello from VM2' | sudo tee /var/www/html/index.html"
                            "sudo systemctl restart nginx"
    })

# Export the Public IP Address
pulumi.export('public_ip', public_ip.ip_address)
