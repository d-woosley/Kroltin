packer {
  required_plugins {
    virtualbox = {
      version = ">= 1.0.0"
      source  = "github.com/hashicorp/virtualbox"
    }
    vmware = {
      version = ">= 1.0.0"
      source  = "github.com/hashicorp/vmware"
    }
  }
}
locals { version = formatdate("YYYY.MM.DD", timestamp()) }

variable "name"                 { type = string }
variable "vm_type"              { type = list(string) }
variable "cpus"                 { type = number }
variable "memory"               { type = number }
variable "disk_size"            { type = number }
variable "ssh_username"         { type = string }
variable "ssh_password"         { type = string }
variable "isos"                 { type = list(string) }
variable "iso_checksum"         { type = string }
variable "scripts"              { type = list(string) }
variable "preseed_file"         { type = string }
variable "http_directory"       { type = string}
variable "export_path"          { type = string }
variable "build_path"           { type = string }
variable "headless"             { type = bool }
variable "guest_os_type"        { type = string }
variable "vmware_version"       { type = number }
variable "source_vmx_path"      { type = string }

source "virtualbox-iso" "vm" {
  boot_command = [
    "<esc><wait>",
    "install auto=true priority=critical vga=788 --- quiet ",
    "ipv6.disable_ipv6=1 net.ifnames=0 biosdevname=0 ",
    "locale=en_US ","keymap=us ",
  "preseed/url=http://{{ .HTTPIP }}:{{ .HTTPPort }}/${var.preseed_file} ",
    "<enter>"
  ]

  boot_wait            = "10s"
  communicator         = "ssh"
  vm_name              = "${var.name}"
  cpus                 = var.cpus
  memory               = var.memory
  disk_size            = var.disk_size
  iso_urls             = var.isos
  iso_checksum         = var.iso_checksum
  guest_os_type        = var.guest_os_type
  headless             = var.headless
  http_directory       = var.http_directory
  ssh_username         = var.ssh_username
  ssh_password         = var.ssh_password
  ssh_port             = "22"
  ssh_timeout          = "3600s"
  hard_drive_interface = "sata"
  vboxmanage           = [["modifyvm","{{ .Name }}","--vram","64"]]
  keep_registered      = true
  output_directory     = "${var.build_path}"
  shutdown_command     = "echo '${var.ssh_password}' | sudo -S shutdown -P now"
}

source "vmware-iso" "vm" {
  boot_command = [
    "<esc><wait>",
    "install auto=true priority=critical vga=788 --- quiet ",
    "ipv6.disable_ipv6=1 net.ifnames=0 biosdevname=0 ",
    "locale=en_US ", "keymap=us ",
    "preseed/url=http://{{ .HTTPIP }}:{{ .HTTPPort }}/${var.preseed_file} ",
    "<enter>"
  ]
  boot_wait            = "10s"
  communicator         = "ssh"
  vm_name              = "${var.name}"
  cpus                 = var.cpus
  memory               = var.memory
  disk_size            = var.disk_size
  iso_urls             = var.isos
  iso_checksum         = var.iso_checksum
  headless             = var.headless
  http_directory       = var.http_directory
  ssh_username         = var.ssh_username
  ssh_password         = var.ssh_password
  ssh_port             = 22
  ssh_timeout          = "3600s"
  vnc_disable_password = true
  vnc_bind_address     = "127.0.0.1"
  vmx_data_post        = {
                          "virtualHW.version": "${var.vmware_version}",
                          "cleanShutdown": "true",
                          "softPowerOff": "true",
                          "ethernet0.virtualDev": "e1000",
                          "ethernet0.startConnected": "true",
                          "ethernet0.wakeonpcktrcv": "false"
                          }
  guest_os_type                   = var.guest_os_type
  vmx_remove_ethernet_interfaces  = false
  version                         = var.vmware_version
  output_directory                = "${var.build_path}"
  shutdown_command                = "echo '${var.ssh_password}' | sudo -S shutdown -P now"
}

build {
  sources = var.vm_type

  provisioner "shell" {
    environment_vars = ["HOME_DIR=/home/${var.ssh_username}"]
    execute_command   = "echo '${var.ssh_password}' | {{ .Vars }} sudo -S -E sh -eux '{{ .Path }}'"
    scripts           = var.scripts
    expect_disconnect = true
  }

  post-processors {
    post-processor "shell-local" {
      only = ["virtualbox-iso.vm"]
      inline = [
        "VBoxManage export '${var.name}' --output '${var.export_path}.ova'",
        "VBoxManage unregistervm '${var.name}' --delete"
      ]
    }
    post-processor "shell-local" {
      only = ["vmware-iso.vm"]
      inline = [
        "ovftool ${var.source_vmx_path} ${var.export_path}.vmx"
      ]
    }
  }
}