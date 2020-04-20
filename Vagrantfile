Vagrant.configure("2") do |config|
  config.vm.box = "pmevo-artifact"
  config.vm.provider "virtualbox" do |provider|
    provider.name = "pmevo-artifact"
    provider.memory = 4096
    provider.cpus = 2
    # provider.memory = 8192
    # provider.cpus = 4
  end
  config.vm.network :forwarded_port, guest: 80, host: 8080
end

