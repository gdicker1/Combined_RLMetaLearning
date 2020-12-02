There are 4 sata drives per node on the cluster
	
  * sda - 447.1G
  
	- sda1 - 298G as xfs mounted to "/"
		
  - sda2 - 128G formerly swap
	
  *sdb - 931.5G unpartitioned as ext4 and unmounted
	
  *sdc - 931.5G unpartitioned as ext4 and unmounted
	
  *sdd - 931.5G unpartitioned as ext4 and unmounted

I want to create a logical volume using sd{b-d} and mount it to /scratch

# Checking for Partition on Each Disk
As root run `blkid` to see that sd{b-d} are all ext4

# Create logical volume from the disks
Following guide at: https://askubuntu.com/questions/7002/how-to-set-up-multiple-hard-drives-as-one-volume/7841#7841 as of 2 Dec 2020

## First repartition as Linux LVM type
The disks need to be partitioned as Linux LVM
	
	sudo fdisk ${drive to parition}

Then select`p` to partition (delete any existing) and `n` to create a new parition. Make it primary with `p` and set number to `1`. Let the sectors be default. Once the parition is set, press `t` and type `8e` to change the parition type to Linux LVM. Finally press `w` to write the changes.

Repeat this for all the disks

## Then, physical volumes
From here following: https://serverfault.com/questions/692724/how-can-i-create-one-large-partiton-over-two-drives-in-centos

Use `pvcreate` to make all the physical volumes needed.

	pvcreate /dev/sdb1 /dev/sdc1 /dev/sdd1


## Then, a volume group

	vgcreate VG_DATA /dev/sdb1 /dev/sdc1 /dev/sdd1

## Then a logical volume

	lvcreate -l 100%FREE -n DATA VG_DATA

## Finally a xfs filesystem in the volume (to match sda1)

	mkfs.xfs /dev/VG_DATA/DATA
	mount /dev/VG_DATA/DATA /scratch
