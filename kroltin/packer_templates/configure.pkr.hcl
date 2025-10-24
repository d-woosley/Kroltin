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
    hyperv = {
      version = ">= 1.0.0"
      source  = "github.com/hashicorp/hyperv"
    }
  }
}
locals { version = formatdate("YYYY.MM.DD", timestamp()) }


variable "name"             { type = string }
variable "vm_file"          { type = string }
variable "vm_type"          { type = list(string) }
variable "ssh_username"     { type = string }
variable "ssh_password"     { type = string }
variable "scripts"          { type = list(string) }
variable "export_path"      { type = string }
variable "build_path"       { type = string }
variable "headless"         { type = bool }
variable "export_file_type" { type = string }
variable "source_vmx_path"  { type = string }

source "virtualbox-ovf" "vm" {
  source_path = var.vm_file
  vm_name = var.name
  communicator = "ssh"
  ssh_username = var.ssh_username
  ssh_password = var.ssh_password
  headless    = var.headless
  ssh_timeout = "10m"
  vboxmanage           = [["modifyvm","{{ .Name }}","--vram","64"]]
  keep_registered      = true
  output_directory     = "${var.build_path}"
  shutdown_command     = "sudo shutdown -P now"
}

source "vmware-vmx" "vm" {
  source_path      = var.vm_file
  vm_name          = var.name
  communicator     = "ssh"
  ssh_username     = var.ssh_username
  ssh_password     = var.ssh_password
  headless         = var.headless
  ssh_timeout      = "10m"
  output_directory = "${var.build_path}"
  shutdown_command = "sudo shutdown -P now"
}

build {
  sources = var.vm_type

  # Grant temporary NOPASSWD sudo for shutdown to handle password changes during provisioning
  provisioner "shell" {
    inline = [
      "echo '${var.ssh_password}' | sudo -S sh -c 'echo \"${var.ssh_username} ALL=(ALL) NOPASSWD: /sbin/shutdown\" >> /etc/sudoers.d/packer-shutdown'",
      "echo '${var.ssh_password}' | sudo -S chmod 0440 /etc/sudoers.d/packer-shutdown"
    ]
  }

  provisioner "shell" {
    environment_vars = ["HOME_DIR=/home/${var.ssh_username}"]
    execute_command   = "echo '${var.ssh_password}' | {{ .Vars }} sudo -S -E sh -eux '{{ .Path }}'"
    scripts           = var.scripts
    expect_disconnect = true
  }

  # Clean up the temporary sudoers file (optional, for security)
  provisioner "shell" {
    inline = [
      "sudo rm -f /etc/sudoers.d/packer-shutdown || true"
    ]
  }

  post-processors {
    post-processor "shell-local" {
      only = ["virtualbox-ovf.vm"]
      inline = [
        "VBoxManage export '${var.name}' --output '${var.export_path}.${var.export_file_type}' || true",
        "VBoxManage unregistervm '${var.name}'"
      ]
    }
    post-processor "shell-local" {
      only = ["vmware-vmx.vm"]
      inline = [
        "ovftool '${var.source_vmx_path}' '${var.export_path}.${var.export_file_type}' || true"
      ]
    }
  }
}