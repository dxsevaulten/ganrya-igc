# reg.rb
module Kicawmania101
  DIR = File.dirname(__FILE__)
  def self.load_components
    require File.join(DIR, 'core.rb')
    require File.join(DIR, 'ui_bridge.rb')
    create_menu
    puts "Marsekeplar v6.0 Kernel loaded."
  end
  def self.create_menu
    UI.menu('Extensions').add_item('Marsekeplar v6.0') { show_transisi_dialog }
    UI.menu('Extensions').add_item('Import Hasil Marsekeplar (Manual)') { import_hasil }
    UI.menu('Extensions').add_separator
    UI.menu('Extensions').add_item('Reload Plugin') { reload_plugin }
  end
  def self.reload_plugin
    Dir.glob(File.join(DIR, '*.rb')).each { |f| load f }
    create_menu
    puts "Plugin Marsekeplar berhasil dimuat ulang."
  end
  load_components
end