makingKubernetes Cluster

following guide:https://kubernetes.io/docs/setup/production-environment/
as of 30 Nov. 2020

Using OPALHPC-1 as the control-plane node
Using OPALHPC-{2,3,5,6} as the worker nodes (Kubelets)

# Contents
* Needed to Install
	* Kubernetes Requirements
* Installing Docker
* Verify MAC address and product_uuid are unique for every node
* Letting iptables see bridged traffic
* Set ports to open [skipped]
* Disable Swap
* Installing kubeadm, kubelet and kubectl
* Creating Control Plane and First Install Verification



## Needed to install
* Docker on all machines
* kubadm, kubectl, kubelet, kubernetes-cni on all machines

### Kubernetes Requirements
* One or more machines running one of:
    - Ubuntu 16.04+
    - Debian 9+
    - CentOS 7 [check]
    - Red Hat Enterprise Linux (RHEL) 7
    - Fedora 25+
    - HypriotOS v1.0.1+
    - Flatcar Container Linux (tested with 2512.3.0)
* 2 GB or more of RAM per machine (any less will leave little room for your apps) [check]
* 2 CPUs or more [check]
* Full network connectivity between all machines in the cluster (public or private network is fine) [should have]
* Unique hostname, MAC address, and product_uuid for every node. [check]
* Certain ports are open on your machines. [need to do]
* Swap disabled. You MUST disable swap in order for the kubelet to work properly. [need to do]

## Installing Docker
Following guide at: https://kubernetes.io/docs/setup/production-environment/container-runtimes/#docker

Install required packages
    
    sudo yum install -y yum-utils device-mapper-persistent-data lvm2
    
Add the Docker repo

	sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

Install Docker

	sudo yum update -y && sudo yum install -y \
	  containerd.io-1.2.13 \
	  docker-ce-19.03.11 \
	  docker-ce-cli-19.03.11

Create /etc/docker and set up the Docker daemon

	sudo mkdir /etc/docker
	cat <<EOF | sudo tee /etc/docker/daemon.json
	{
	  "exec-opts": ["native.cgroupdriver=systemd"],
	  "log-driver": "json-file",
	  "log-opts": {
	    "max-size": "100m"
	  },
	  "storage-driver": "overlay2",
	  "storage-opts": [
	    "overlay2.override_kernel_check=true"
	  ]
	}
	EOF
	
Create `/etc/systemd/system/docker.service.d`
	
	sudo mkdir -p /etc/systemd/system/docker.service.d

Restart Docker

	sudo systemctl daemon-reload
	sudo systemctl restart docker

Run docker on boot

	sudo systemctl enable docker

## Verify MAC address and product_uuid are unique for every node
* Use `ip link` or `ifconfig -a` to check the MAC address of every node that is going to be in the cluster
* The product_uuid's can be checked using `sudo cat /sys/class/dmi/id/product_uuid`

## Letting iptables see bridged traffic
Ensure br_netfilter is loaded

	lsmod | grep br_netfilter
	
Load it if not
	
	sudo modprobe br_netfilter

Set `net.bridge.bridge-nf-call-iptables` in `sysctl` config
	
	cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
	net.bridge.bridge-nf-call-ip6tables = 1
	net.bridge.bridge-nf-call-iptables = 1
	EOF
	sudo sysctl --system
	
	
## Set ports to open [skipped]
!!! Actually can skip this because the OPALHPC aren't running `firwalld` !!!

Kubernetes needs certain ports open

For control-plane nodes
| Protocol| Direction | Port Range | Purpose | Used By |
| --- | --- | --- | --- | --- |
| TCP | Inbound | 6443* | Kubernetes API server | All |
| TCP | Inbound | 2379-2380 | etcd server client API | kube-apiserver, etcd |
| TCP | Inbound | 10250 | Kubelet API | Self, Control plane |
| TCP | Inbound | 10251 | kube-scheduler | Self |
| TCP | Inbound | 10252 | kube-controller-manager | Self |

For worker nodes
| Protocol| Direction | Port Range | Purpose | Used By |
| --- | --- | --- | --- | --- |
| TCP |Inbound |10250 | Kubelet API | Self, Control plane |
| TCP | Inbound | 30000-32767 | NodePort Services† | All |

Steps:
	1. Ensure port is open
		`netstat -na | grep ${PORT_NUMBER}`
		`iptables-save | grep ${PORT_NUMBER}`
	2. Edit `/etc/services` and allow the port to accept packets using the format "service-name  port/protocol  [aliases ...]   [# comment]"

## Disable Swap
First visualize memory

	free -h

Swap can probably be disabled if near 0B are being used

Then look for `[SWAP]` in the MOUNTPOINT column of the next command

	lsblk

For OpalHPC-1 this was /dev/sda2. There were also /dev/sdb, /dev/sdc, and /dev/sdd

Running the swapoff command will deactivate the swap

	swapoff /dev/sda2

Then comment out the line in the `/etc/fstab` file that mentions the swap type
	
	vi /etc/fstab

Reboot or remount all
	
	sudo reboot
	# or mount -a

### Revert swap [not carried out yet]
Current partition scheme on OpalHPC-1
	
	fdisk /dev/sda
	>p # show partitions on drive
	Disk /dev/sda: 480.1 GB, 480103981056 bytes, 937703088 sectors
	Units = sectors of 1 * 512 = 512 bytes
	Sector size (logical/physical): 512 bytes / 512 bytes
	I/O size (minimum/optimal): 512 bytes / 512 bytes
	Disk label type: dos
	Disk identifier: 0x000bd5eb
	   Device Boot      Start         End      Blocks   Id  System
	/dev/sda1   *        2048   625000447   312499200   83  Linux
	/dev/sda2       625000448   893435903   134217728   82  Linux swap / Solaris

So `/dev/sda2` currently is using 131072 MiB = 128 GB (a block is a MiB) for the swap partition

Create new partition (potentially)
	
	fdisk
	>p # list partitions
	>n # make new partition
	>p # make primary partition (?)
	>+128G # make partition 128 GiB

Create the swap association for the new partition
	
	mkswap /dev/sdc1

Use the UUID from the previous command to add an entry to `/etc/fstab`

	vi /etc/fstab
	UUID=${UUID}     swap     swap     defaults	

Activate the swap partition and verify its presence

	swapon -a
	swapon -s

## Installing kubeadm, kubelet and kubectl
The components are:
* `kubeadm`: the command to bootstrap the cluster.
* `kubelet`: the component that runs on all of the machines in your cluster and does things like starting pods and containers.
* `kubectl`: the command line util to talk to your cluster

Add the Kubernetes repo

	cat <<EOF | sudo tee /etc/yum.repos.d/kubernetes.repo
	[kubernetes]
	name=Kubernetes
	baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-\$basearch
	enabled=1
	gpgcheck=1
	repo_gpgcheck=1
	gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
	exclude=kubelet kubeadm kubectl
	EOF

Set SELinux in permissive mode (effectively disabling it). The default setting was `setenforce 1` and `SELINUX=enforcing`

	sudo setenforce 0
	sudo sed -i 's/^SELINUX=enforcing$/SELINUX=permissive/' /etc/selinux/config

Install the components

	sudo yum install -y kubelet kubeadm kubectl --disableexcludes=kubernetes

Enable the service to start at startup

	sudo systemctl enable --now kubelet

## Install a Container Network Interface (CNI)
I chose Calico, but others can be found at https://kubernetes.io/docs/concepts/cluster-administration/addons/

Calico instructions at: https://docs.projectcalico.org/getting-started/kubernetes/quickstart

### Initialize the master node (control plane) with a particular CIDR mask. Lets use /24
	
	kubeadm init --pod-network-cidr=192.168.0.0/16
	
	kubeadm init

Output:
	
	Your Kubernetes control-plane has initialized successfully!
	To start using your cluster, you need to run the following as a regular user:
	  mkdir -p $HOME/.kube
	  sudo scp -i root@opalhpc-1/etc/kubernetes/admin.conf $HOME/.kube/config
	  sudo chown $(id -u):$(id -g) $HOME/.kube/config
	You should now deploy a pod network to the cluster.
	Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
	  https://kubernetes.io/docs/concepts/cluster-administration/addons/
	Then you can join any number of worker nodes by running the following on each as root:
	kubeadm join 10.2.22.41:6443 --token kheflh.hze5jlr3zp6vhpzz \
	    --discovery-token-ca-cert-hash sha256:c659fc2420aef62234cbd7b5e3e4934d2f165dfb0a5aa06d24428ed1f4dd730f


### Join a node

	kubeadm join 10.2.22.41:6443 --token kheflh.hze5jlr3zp6vhpzz \
	    --discovery-token-ca-cert-hash sha256:c659fc2420aef62234cbd7b5e3e4934d2f165dfb0a5aa06d24428ed1f4dd730f

Set role to worker

	kubectl label node opalhpc-2 node-role.kubernetes.io/worker=worker

Log on as a regular user with sudo privileges to setup kubeadmin
	
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

Download the Calico networking manifest for Kubernetes API datastore

	curl https://docs.projectcalico.org/manifests/calico.yaml -O

Install Calico by creating a custom resource

	kubectl apply -f calico.yaml

Change Calico to try to find opalhpc-1 for the auto-IP

	kubectl set env daemonset/calico-node -n kube-system IP_AUTODETECTION_METHOD=can-reach=opalhpc-1


## Verify with sonobuoy (master node)
Download the correct sonobuoy tarball, extract it, and add the sonobuoy executable to the path

Run the quick check with

	sonobuoy run --mode quick

Retrieve results tarball with
	
	sonobuoy retrieve

Then view the logs
