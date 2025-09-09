locals { version = formatdate("YYYY.MM.DD", timestamp()) }

variable "name"         { type = string }
variable "vm_file"      { type = string }
variable "ssh_username" { type = string }
variable "ssh_password" { type = string }
variable "scripts"      { type = list(string) }
variable "export_path"  { type = string }

source "virtualbox-ovf" "import" {
  source_path = var.ovf_file
  vm_name = var.name
  communicator = "ssh"
  ssh_username = var.ssh_username
  ssh_password = var.ssh_password
  headless    = true
  ssh_timeout = "10m"
  vboxmanage           = [["modifyvm","{{ .Name }}","--vram","64"]]
  keep_registered      = false
  output_directory     = "${var.export_path}"
  shutdown_command     = "echo '${var.ssh_password}' | sudo -S shutdown -P now"
}

build {
  sources = ["source.virtualbox-ovf.import"]

  provisioner "shell" {
    environment_vars = ["HOME_DIR=/home/${var.ssh_username}"]
    execute_command   = "echo '${var.ssh_password}' | {{ .Vars }} sudo -S -E sh -eux '{{ .Path }}'"
    scripts           = var.scripts
    expect_disconnect = true
  }

  post-processors {
    post-processor "shell-local" {
      inline = [
        "VBoxManage export '${var.name}' --output '${var.export_path}/${var.name}-${local.version}.ova'",
        "sha256sum '${var.export_path}/${var.name}-${local.version}.ova' > '${var.export_path}/${var.name}-${local.version}.ova.sha256'",
        "VBoxManage unregistervm '${var.name}' --delete || true"
      ]
    }
  }
}