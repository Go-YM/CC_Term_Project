import boto3
import time
from botocore.exceptions import WaiterError

access_key = ""
secret_key = ""

global ec2
global resource
global ssm
global cw

def init_aws():
    global ec2
    global resource
    global ssm
    global cw

    ec2 = boto3.client('ec2', aws_access_key_id = access_key, aws_secret_access_key = secret_key, region_name = "us-west-1")
    ssm = boto3.client('ssm', aws_access_key_id = access_key, aws_secret_access_key = secret_key, region_name = "us-west-1")
    resource = boto3.resource('ec2', aws_access_key_id = access_key, aws_secret_access_key = secret_key, region_name = "us-west-1")
    cw = boto3.client('cloudwatch', aws_access_key_id = access_key, aws_secret_access_key = secret_key, region_name = "us-west-1")
    
def list_instances():
    print("Listing instances...")
    done = False
    while done == False:
        list = resource.instances.all()
        for instance in list:
            print("[id] %s, [AMI] %s, [type] %s, [state] %10s, [monitoring state] %s" % (instance.instance_id, instance.image_id, instance.instance_type, instance.state['Name'], instance.monitoring['State']))
        done=True

def available_zones():
    print("Available zones...")
    done = False
    while done == False:
        res = ec2.describe_availability_zones()
        list = res['AvailabilityZones']
        for zone in list:
            print("You have access to [id] %s  [region] %15s [zone] %15s Availability Zones.\n" % (zone['ZoneId'], zone['RegionName'], zone['ZoneName']))
        done=True

def start_instance(id):
    print("Starting ... %s" % id)
    done= False
    while done == False:
        res = ec2.start_instances(InstanceIds = [id])
        instance = resource.Instance(id)
        instance.wait_until_running(Filters = [{'Name': 'instance-id','Values':[id]}])
        print("Successfully started instance %s" % id)
        done = True

def available_regions():
    print("Available regions...")
    done = False
    while done == False:
        res = ec2.describe_regions()
        list = res['Regions']
        for region in list:
            print("[region] %15s, [endpoint] %s" % (region['RegionName'], region['Endpoint']))
        done = True

def stop_instance(id):
    print("Stopping ... %s" % id)
    done = False
    while done == False:
        res = ec2.stop_instances(InstanceIds = [id])
        instance = resource.Instance(id)
        instance.wait_until_stopped(Filters = [{'Name': 'instance-id','Values':[id]}])
        print("Successfully stopped instance %s" % id)
        done = True

def create_instance(id):
     print("Creating...")
     done = False
     while done == False:
        res = resource.create_instances(ImageId=id, InstanceType = 't2.micro', MaxCount=1, MinCount=1, SecurityGroupIds = ['sg-0aea1701a877c2c1d'])
        instance = resource.Instance(res[0].instance_id)
        instance.wait_until_running(Filters = [{'Name': 'instance-id','Values':[res[0].instance_id]}])
        print("Successfully started EC2 instance %s based on AMI %s" % (res[0].instance_id, id))
        done = True

def reboot_instance(id):
    print("Rebooting ... %s" % id)
    done = False
    while done == False:
        res = ec2.reboot_instances(InstanceIds = [id])
        instance = resource.Instance(id)
        instance.wait_until_running(Filters = [{'Name': 'instance-id','Values':[id]}])
        print("Successfully rebooted instance %s" % id)
        done = True

def terminate_instance(id):
    print("Terminating ... %s" % id)
    done = False
    while done == False:
        if id == 'i-0b11d6ef1f13f1d4a' or id == 'i-02eec58bda8af1423':
            print('Don\'t delete this Instance!!!')
            break
        res = ec2.terminate_instances(InstanceIds = [id])
        instance = resource.Instance(id)
        instance.wait_until_terminated(Filters = [{'Name': 'instance-id','Values':[id]}])
        print("Successfully terminated instance %s" % id)
        done = True

def monitor_instance(id, max, interval = 60):
    print("Monitoring ... %s" % id)
    done = False
    while done == False:
        res = cw.get_metric_statistics(Namespace='AWS/EC2', MetricName='CPUUtilization', Dimensions=[{'Name': 'InstanceId', 'Value': id}], StartTime=time.time() - 300, EndTime=time.time(), Period=60, Statistics=['Average'])
        datapoints = res.get('Datapoints', [])
        if datapoints:
            cpu_utilization = sorted(datapoints, key=lambda x: x['Timestamp'], reverse=True)[0]['Average']
            print(f"Instance {id} CPU utilization: {cpu_utilization:.2f} %")
            if cpu_utilization > max:
                print(f"CPU utilization exceeded %s%. Stopping instance %s..." % (max, id))
                ec2.stop_instances(InstanceIds=[id])
                print(f"Successfully stopped Instance %s" % id)
                break
        else:
            print(f"No CPU utilization data available for instance %s" % id)
        done = True
        
def unmonitor_instance(id):
    print("Unmonitoring...%s" % id)
    done = False
    while done == False:
        res = ec2.unmonitor_instances(InstanceIds=[id])
        print(f"Successfully unmonitoring for instance %s" % id)
        done = True
    

def list_images():
    print("Listing images ...")
    done = False
    while done == False:
        res = ec2.describe_images(Filters = [{'Name':'name','Values':['aws-htcondor-slave']}])
        list = res['Images']
        for image in list:
            print("[ImageID] %s, [Name] %s, [Owner] %s" % (image['ImageId'], image['Name'], image['OwnerId']))
        done = True
        
def list_security_group():
    print("Listing security group ...")
    done = False
    while done == False:
        res = ec2.describe_security_groups(Filters = [{'Name':'owner-id','Values':['767828727609']}])
        security_groups = res['SecurityGroups']
        for sg in security_groups:
            print("[GroupID] %s, [GroupName] %s, [Owner] 767828727609" % (sg['GroupId'], sg['GroupName']))
        done = True

def create_security_group():
    print("Creating security group ...")
    res = ec2.describe_vpcs()
    vpc_id = res.get('Vpcs', [{}])[0].get('VpcId', '')
    done = False
    while done == False:
        print("Enter Security Group Name: ", end="")
        Gname = input()
        print("Enter Security Group Description: ", end="")
        Gdes = input()
        print("Enter Type of IpProtocol (Default = tcp): ", end="")
        Iptype = input()
        if Iptype == '':
            Iptype = 'tcp'
        print("Enter Pronunciation of Port: ", end="")
        fromport = int(input())
        print("Enter Destination of Port: ", end="")
        toport = int(input())
        print("Enter Address of IP: (Defualt = 0.0.0.0/0): ", end="")
        cidrip = input()
        
        res = ec2.create_security_group(GroupName = Gname, Description = Gdes, VpcId = vpc_id)
        security_group_id = res['GroupId']
        data = ec2.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[{'IpProtocol': Iptype,'FromPort': fromport,'ToPort': toport,'IpRanges': [{'CidrIp': cidrip}]}])
        print("Successfully created Security Group %s in vpc %s" % (security_group_id, vpc_id))
        done = True
        
def delete_security_group(Gname):
    print("Deleting security group ...")
    done = False
    while done == False:
        if Gname == 'default' or Gname == 'HTCondor':
            print('Don\'t delete this Security Group!!!')
            break
        res = ec2.delete_security_group(GroupName=Gname)
        print('Successfully deleted Security Group %s' % Gname)
        done = True
        
def condor_status(id):
    print("Listing condor status ...")
    res = ssm.send_command(InstanceIds = [id], DocumentName = 'AWS-RunShellScript', Parameters = {'commands': ['condor_status']})
    command_id = res['Command']['CommandId']

    waiter = ssm.get_waiter("command_executed")
    try:
        waiter.wait(
        CommandId = command_id,
        InstanceId = 'i-0b11d6ef1f13f1d4a',
        )
    except WaiterError as ex:
        logging.error(ex)
        return

    print(ssm.get_command_invocation(CommandId = command_id, InstanceId = id)['StandardOutputContent']) 
    
def list_snapshot():
    print("Listing snapshot...")
    done = False
    while done == False:
        res = ec2.describe_snapshots(Filters = [{'Name':'owner-id','Values':['767828727609']}])
        snapshots = res['Snapshots']
        for ss in snapshots:
            print("[Snapshot ID] %s, [Volume] %s, [State] %s, [Description] %s" % (ss['SnapshotId'], ss['VolumeId'], ss['State'], ss['Description']))
            done = True

def create_snapshot(id):
    print("Creating snapshot...")
    done = False
    while done == False:
        instance_details = ec2.describe_instances(InstanceIds=[id])
        volumes = [
            block_device['Ebs']['VolumeId']
            for reservation in instance_details['Reservations']
            for instance in reservation['Instances']
            for block_device in instance.get('BlockDeviceMappings', [])
            if 'Ebs' in block_device
        ]
        if not volumes:
            print(f"No EBS volumes found for instance %s" % id)
            return
        for volume_id in volumes:
            print(f"Creating snapshot for volume %s..." % volume_id)
            snapshot = ec2.create_snapshot(
                VolumeId=volume_id,
                Description=f"Snapshot of volume %s from instance %s" % (volume_id, id)
            )
            print("Successfully created Snapshot %s" % snapshot['SnapshotId']) 
        done = True

def delete_snapshot(id):
    print("Deleting snapshot...")
    done = False
    while not done:
        images = ec2.describe_images(Filters=[{"Name": "block-device-mapping.snapshot-id", "Values": [id]}])
        if images['Images']:
            print(f"Snapshot %s is being used by the following AMIs:" % id)
            for image in images['Images']:
                print(f"  - AMI ID: %s, Name: %s" % (image['ImageId'], image['Name']))
                print(f"Deregistering AMI %s..." % image['ImageId'])
                ec2.deregister_image(ImageId=image['ImageId'])
            print(f"All AMIs using snapshot %s have been deregistered" % id)

        try:
            ec2.delete_snapshot(SnapshotId=id, DryRun=False)
            print(f"Successfully deleted snapshot %s" % id)
            done = True
        except Exception as e:
            print(f"Failed to delete snapshot %s: %s" %(id, e))
            done = True

if __name__ == "__main__":
    init_aws()
    while True:
        print("------------------------------------------------------------")
        print("        Amazon AWS Control Panel using SDK - Main           ")
        print("------------------------------------------------------------")
        print("  1. Instance                     2. Abailiability          ")
        print("  3. Security Group               4. Snapshot               ")
        print("                                                            ")
        print("  00. back                        99. exit                  ")
        print("------------------------------------------------------------")

        print("Enter a number: ",end="")
        num = int(input())

        if num == 1:
            while True:
                print("------------------------------------------------------------")
                print("      Amazon AWS Control Panel using SDK - Instance         ")
                print("------------------------------------------------------------")
                print("  1. list instance                2. list images            ")
                print("  3. start instance               4. stop instance          ")
                print("  5. reboot instance              6. create instance        ")
                print("  7. monitor instance             8. unmonitor instance     ")
                print("  9. terminate instance           10. condor status         ")
                print("                                                            ")
                print("  00. back                        99. exit                  ")
                print("------------------------------------------------------------")

                print("Enter a number: ",end="")
                num = int(input())
                
                if num == 1:
                    list_instances()
        
                elif num == 2:
                    list_images()

        
                elif num == 3:
                    print("Enter instance id: ",end="")
                    id = input()
                    start_instance(id)                

                    
                elif num == 4:
                    print("Enter instance id: ",end="")
                    id = input()
                    stop_instance(id)                

        
                elif num == 5:
                    print("Enter instance id: ",end="")
                    id = input()
                    reboot_instance(id)                
        
                elif num == 6:
                    print("Enter ami id: ",end="")
                    id = input()
                    create_instance(id)
        
                elif num == 7:
                    print("Enter instance id: ",end="")
                    id = input()
                    print("Enter threshold of cpu utilization: ",end="")
                    max = int(input())
                    monitor_instance(id, max)

                elif num == 8:
                    print("Enter instance id: ",end="")
                    id = input()
                    unmonitor_instance(id)

                elif num == 9:
                    print("Enter instance id: ",end="")
                    id = input()
                    terminate_instance(id)
                    
                elif num == 10:
                    print("Enter instance id: ",end="")
                    id = input()
                    condor_status(id)
                    
                elif num == 99:
                    exit(0)
            
                elif num == 00:
                    break
                    
                else:
                    print("concertration!")
        
        elif num == 2:
            while True:
                print("------------------------------------------------------------")
                print("     Amazon AWS Control Panel using SDK - Availability      ")
                print("------------------------------------------------------------")
                print("  1. available zones              2. available regions      ")
                print("                                                            ")
                print("  00. back                        99. exit                  ")
                print("------------------------------------------------------------")

                print("Enter a number: ",end="")
                num = int(input())
                
                if num == 1:
                    available_zones()
        
                elif num == 2:
                    available_regions()
                    
                elif num == 99:
                    exit(0)
            
                elif num == 00:
                    break
                    
                else:
                    print("concertration!")
        
        elif num == 3:
            while True:
                print("------------------------------------------------------------")
                print("   Amazon AWS Control Panel using SDK - Security Group      ")
                print("------------------------------------------------------------")
                print("  1. list security group          2. create security group  ")
                print("  3. delete security group                                  ")
                print("                                                            ")
                print("  00. back                        99. exit                  ")
                print("------------------------------------------------------------")

                print("Enter a number: ",end="")
                num = int(input())
                
                if num == 1:
                    list_security_group()
        
                elif num == 2:
                    create_security_group()
                    
                elif num == 3:
                    print("Enter Security Group Name: ",end="")
                    Gname = input()
                    delete_security_group(Gname)
                    
                elif num == 99:
                    exit(0)
            
                elif num == 00:
                    break
                    
                else:
                    print("concertration!")
        
        elif num == 4:
            while True:
                print("------------------------------------------------------------")
                print("      Amazon AWS Control Panel using SDK - Snapshot         ")
                print("------------------------------------------------------------")
                print("  1. list snapshot                2. create snapshot        ")
                print("  3. delete snapshot                                        ")
                print("                                                            ")
                print("  00. back                        99. exit                  ")
                print("------------------------------------------------------------")

                print("Enter a number: ",end="")
                num = int(input())
                
                if num == 1:
                    list_snapshot()
        
                elif num == 2:
                    print("Enter instance id: ",end="")
                    id = input()
                    create_snapshot(id)
                    
                elif num == 3:
                    print("Enter snapshot id: ",end="")
                    id = input()
                    delete_snapshot(id)
                    
                elif num == 99:
                    exit(0)
            
                elif num == 00:
                    break
                    
                else:
                    print("concertration!")
            
        elif num == 99:
            exit(0)
            
        elif num == 00:
            print("can\'t back here")
            
        else:
            print("concertration!")
