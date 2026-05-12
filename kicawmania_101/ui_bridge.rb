# ui_bridge.rb - Jembatan antara SketchUp dan GUI Python
module Kicawmania101
  # PYTHON_EXE dan ENGINE_SCRIPT sudah didefinisikan di core.rb, jadi tidak perlu di sini.

  def self.launch_gui(data_hash)
    temp_dir = Dir.tmpdir
    input_path = File.join(temp_dir, "skp_package_gui_#{Time.now.to_i}.json")
    File.write(input_path, JSON.generate(data_hash))

    python_cmd = "\"#{PYTHON_EXE}\" \"#{ENGINE_SCRIPT}\" \"#{input_path}\""
    puts "Meluncurkan GUI Holographic: #{python_cmd}"
    pid = Process.spawn(python_cmd)
    Process.detach(pid)
  end
end