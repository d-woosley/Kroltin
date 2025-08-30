locals { version = formatdate("YYYY.MM.DD", timestamp()) }

variable "name"       { type = string }
variable "cpus"         { type = number }
variable "memory"       { type = number }
variable "disk_size"    { type = number }
variable "ssh_username" { type = string }
variable "ssh_password" { type = string }
variable "iso_urls"     { type = list(string) }
variable "iso_checksum" { type = string }
variable "scripts"      { type = list(string) }
variable "preseed_file" { type = string }

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
  iso_urls             = var.iso_urls
  iso_checksum         = var.iso_checksum
  guest_os_type        = "Debian_64"
  headless             = true
  http_directory       = "preseed-files"
  ssh_username         = var.ssh_username
  ssh_password         = var.ssh_password
  ssh_port             = "22"
  ssh_timeout          = "3600s"
  hard_drive_interface = "sata"
  vboxmanage           = [["modifyvm","{{ .Name }}","--vram","64"]]
  keep_registered      = true
  output_directory     = "${var.name}"
  shutdown_command     = "echo '${var.ssh_password}' | sudo -S shutdown -P now"
}

build {
  sources = ["source.virtualbox-iso.vm"]

  provisioner "shell" {
    environment_vars = ["HOME_DIR=/home/${var.ssh_username}"]
    execute_command   = "echo '${var.ssh_password}' | {{ .Vars }} sudo -S -E sh -eux '{{ .Path }}'"
    scripts           = var.scripts
    expect_disconnect = true
  }

  post-processors {
    post-processor "shell-local" {
      inline = [
        "VBoxManage export '${var.name}' --output '${var.name}-${local.version}.ova'",
        "sha256sum '${var.name}-${local.version}.ova' > '${var.name}-${local.version}.ova.sha256'",
        "VBoxManage unregistervm '${var.name}' --delete || true"
      ]
    }
  }
}
