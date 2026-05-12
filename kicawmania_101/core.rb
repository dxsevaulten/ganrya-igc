# kicawmania_101/core.rb
module Kicawmania101
  PYTHON_EXE = "C:/Google Drive/venv_skp_engine/Scripts/python.exe"
  ENGINE_SCRIPT = File.join(File.dirname(__FILE__), '..', 'engine_gui.py')

  # -----------------------------------------------------------------
  # Reload otomatis
  # -----------------------------------------------------------------
  def self.reload_plugin
    path = File.join(File.dirname(__FILE__), 'core.rb')
    if File.exist?(path)
      load path
      puts "Plugin Marsekeplar berhasil dimuat ulang."
    else
      UI.messagebox("File core tidak ditemukan.")
    end
  end

  # -----------------------------------------------------------------
  # Dialog GUI
  # -----------------------------------------------------------------
  def self.show_transisi_dialog
    html = <<~HTML
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body { font-family: Arial; padding: 15px; background: #f5f5f5; }
          h2 { color: #2c3e50; }
          button { padding: 10px 20px; margin-top: 15px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; }
          .section { margin: 10px 0; }
        </style>
      </head>
      <body>
        <h2>Transisi Marsekeplar v6.0</h2>
        <p><i>Proyeksi 2D → GUI Holographic → Auto-Import</i></p>
        <div class="section">
          <strong>Pilih Sisi:</strong><br>
          <label><input type="checkbox" id="front" checked> Depan</label>
          <label><input type="checkbox" id="back" checked> Belakang</label>
          <label><input type="checkbox" id="left" checked> Kiri</label>
          <label><input type="checkbox" id="right" checked> Kanan</label>
          <label><input type="checkbox" id="top" checked> Atas</label>
          <label><input type="checkbox" id="bottom" checked> Bawah</label>
        </div>
        <button onclick="submit()">Proyeksi ke 2D</button>
        <script>
          function submit() {
            var data = {
              sides: {
                front: document.getElementById('front').checked,
                back: document.getElementById('back').checked,
                left: document.getElementById('left').checked,
                right: document.getElementById('right').checked,
                top: document.getElementById('top').checked,
                bottom: document.getElementById('bottom').checked
              }
            };
            sketchup.send_form_data(JSON.stringify(data));
          }
        </script>
      </body>
      </html>
    HTML

    dlg = UI::HtmlDialog.new(
      dialog_title: "Transisi Marsekeplar v6.0",
      preferences_key: "com.kicawmania.transisi",
      width: 320,
      height: 280
    )
    dlg.set_html(html)
    dlg.add_action_callback("send_form_data") do |_, json_str|
      options = JSON.parse(json_str)
      dlg.close
      self.run_transisi(options)
    end
    dlg.show
  end

  # -----------------------------------------------------------------
  # Proyeksi vertex ke bidang 2D (tanpa Vector3d * Float)
  # -----------------------------------------------------------------
  def self.project_vertices(vertices, normal, ref_point)
    z_local = Geom::Vector3d.new(0,0,1)
    x_local = Geom::Vector3d.new(1,0,0)
    y_local = Geom::Vector3d.new(0,1,0)
    normal_vec = Geom::Vector3d.new(normal[0], normal[1], normal[2])
    
    if normal_vec.parallel?(z_local)
      basis_x = x_local
      basis_y = y_local
    else
      dot_val = z_local.dot(normal_vec)
      # scaled = normal_vec * dot_val  (manual)
      scaled = Geom::Vector3d.new(normal_vec.x * dot_val, normal_vec.y * dot_val, normal_vec.z * dot_val)
      proj_z = z_local - scaled
      if proj_z.length > 1e-6
        basis_y = proj_z.normalize
      else
        basis_y = y_local
      end
      basis_x = normal_vec.cross(basis_y).normalize
    end

    ref_pt = Geom::Point3d.new(ref_point[0], ref_point[1], ref_point[2])
    projected = vertices.map do |v|
      vec = v.vector_to(ref_pt)  # vektor dari ref_point ke vertex
      x = vec.dot(basis_x)
      y = vec.dot(basis_y)
      [x, y]
    end
    projected
  end

  # ----- Plane Preview -----
  def self.draw_plane_preview(sides, normals_data, vertices_list)
    model = Sketchup.active_model
    # Hapus preview lama jika ada (berdasarkan nama material khusus)
    cleanup_plane_preview
    
    ref_point = get_center_of_vertices(vertices_list)
    offset_distance = 100.0
    
    sides.each do |side, checked|
      next unless checked
      normal = normals_data[side]
      normal_vec = Geom::Vector3d.new(normal[0], normal[1], normal[2])
      
      # Posisi bidang = pusat objek + normal * offset
      origin = Geom::Point3d.new(ref_point[0], ref_point[1], ref_point[2])
                          .offset(normal_vec, offset_distance)
      
      # Hitung basis lokal
      z_local = Geom::Vector3d.new(0,0,1)
      if normal_vec.parallel?(z_local)
        basis_x = Geom::Vector3d.new(1,0,0)
        basis_y = Geom::Vector3d.new(0,1,0)
      else
        dot_val = z_local.dot(normal_vec)
        scaled = Geom::Vector3d.new(normal_vec.x * dot_val, normal_vec.y * dot_val, normal_vec.z * dot_val)
        proj_z = z_local - scaled
        basis_y = proj_z.length > 1e-6 ? proj_z.normalize : Geom::Vector3d.new(0,1,0)
        basis_x = normal_vec.cross(basis_y).normalize
      end
      
      # Hitung batas proyeksi untuk ukuran bidang
      proj_2d = project_vertices(vertices_list, normal, ref_point)
      min_x = proj_2d.map { |p| p[0] }.min
      max_x = proj_2d.map { |p| p[0] }.max
      min_y = proj_2d.map { |p| p[1] }.min
      max_y = proj_2d.map { |p| p[1] }.max
      
      # Buat 4 titik sudut bidang
      margin = 20.0
      corners = [
        origin.offset(basis_x, min_x - margin).offset(basis_y, min_y - margin),  # kiri-bawah
        origin.offset(basis_x, max_x + margin).offset(basis_y, min_y - margin),  # kanan-bawah
        origin.offset(basis_x, max_x + margin).offset(basis_y, max_y + margin),  # kanan-atas
        origin.offset(basis_x, min_x - margin).offset(basis_y, max_y + margin)   # kiri-atas
      ]
      
      # Gambar face semi-transparan
      group = model.active_entities.add_group
      face = group.entities.add_face(corners)
      
      # Buat material semi-transparan
      mat_name = "Marsekeplar_PlanePreview"
      mat = model.materials[mat_name] || model.materials.add(mat_name)
      mat.color = Sketchup::Color.new(0, 255, 255)  # Cyan
      mat.alpha = 0.3
      face.material = mat
      face.back_material = mat
      
      # Namai group untuk identifikasi cleanup
      group.name = "Marsekeplar_PlanePreview"
    end
  end

  def self.get_center_of_vertices(vertices_list)
    sum_x = vertices_list.sum { |v| v.x }
    sum_y = vertices_list.sum { |v| v.y }
    sum_z = vertices_list.sum { |v| v.z }
    n = vertices_list.length
    [sum_x / n, sum_y / n, sum_z / n]
  end

  def self.cleanup_plane_preview
    model = Sketchup.active_model
    model.entities.grep(Sketchup::Group).each do |g|
      g.erase! if g.name == "Marsekeplar_PlanePreview"
    end
  end

  # Tambahkan method ini di dekat collect_geometry_with_color
  def self.collect_geometry(ent, vertices_map, vertices_list, edges_list)
    face_colors = []  # dummy
    collect_geometry_with_color(ent, vertices_map, vertices_list, edges_list, face_colors)
  end

  # -----------------------------------------------------------------
  # Eksekusi proyeksi
  # -----------------------------------------------------------------
  def self.run_transisi(options)
    model = Sketchup.active_model
    sel = model.selection
    if sel.empty?
      UI.messagebox("Harap pilih minimal satu objek 3D.")
      return
    end

    # Kumpulkan semua vertex dan edge dari seleksi
    vertices_map = {}
    vertices_list = []
    edges_list = []
    sel.each do |ent|
      collect_geometry(ent, vertices_map, vertices_list, edges_list)
    end

    if vertices_list.empty?
      UI.messagebox("Tidak ada geometri ditemukan.")
      return
    end

    bb = get_bounding_box(sel)
    ref_point = bb ? bb.center.to_a : [0,0,0]

    normals_data = {
      'front'  => [0, 0, -1],
      'back'   => [0, 0, 1],
      'left'   => [-1, 0, 0],
      'right'  => [1, 0, 0],
      'top'    => [0, 0, 1],
      'bottom' => [0, 0, -1]
    }

    projections = {}
    options['sides'].each do |side, checked|
      next unless checked
      normal = normals_data[side]
      proj_2d = project_vertices(vertices_list, normal, ref_point)
      edges_2d = []
      edges_list.each do |i1, i2|
        if i1 < proj_2d.length && i2 < proj_2d.length
          p1 = proj_2d[i1]
          p2 = proj_2d[i2]
          edges_2d << [p1[0], p1[1], p2[0], p2[1]]
        end
      end
      projections[side] = { 'edges_2d' => edges_2d }
    end

    # Simpan hasil proyeksi ke file sementara
    temp_dir = Dir.tmpdir
    input_path = File.join(temp_dir, "skp_projection_#{Time.now.to_i}.json")
    package = {
      'projections' => projections,
      'normals' => normals_data
    }
    File.write(input_path, JSON.generate(package))
    # Di run_transisi, setelah menyimpan JSON dan sebelum panggil GUI:
    draw_plane_preview(options['sides'], normals_data, vertices_list)

    # Panggil GUI Python
    python_cmd = "\"#{PYTHON_EXE}\" \"#{ENGINE_SCRIPT}\" \"#{input_path}\""
    puts "Perintah: #{python_cmd}"
    pid = Process.spawn(python_cmd)
    Process.detach(pid)

    # Mulai pemantau file lock (auto-import)
    start_auto_import_watcher

    UI.messagebox("Proyeksi 2D berhasil dibuat!\n\nGUI Holographic akan terbuka.\nAtur parameter dan klik 'Terapkan ke SketchUp'.")
  end

  # Modifikasi collect_geometry untuk juga mengumpulkan warna
  def self.collect_geometry_with_color(ent, vertices_map, vertices_list, edges_list, face_colors)
    if ent.is_a?(Sketchup::Group) || ent.is_a?(Sketchup::ComponentInstance)
      ent.definition.entities.each { |e| collect_geometry_with_color(e, vertices_map, vertices_list, edges_list, face_colors) }
    elsif ent.is_a?(Sketchup::Face)
      # Ambil warna material
      mat = ent.material
      color = mat ? [mat.color.red, mat.color.green, mat.color.blue] : [255, 255, 255]
      
      # Ambil outer loop vertices
      outer_loop = ent.outer_loop
      vert_indices = []
      outer_loop.vertices.each do |v|
        idx = (vertices_map[v.position] ||= vertices_list.length; vertices_list << v.position; vertices_list.length - 1)
        vert_indices << idx
      end
      
      # Simpan face dengan warnanya
      face_colors << { indices: vert_indices, color: color }
      
      # Tambahkan edge dari outer loop
      (0...vert_indices.length).each do |i|
        i2 = (i + 1) % vert_indices.length
        pair = [vert_indices[i], vert_indices[i2]].sort
        edges_list << pair unless edges_list.include?(pair)
      end
    elsif ent.is_a?(Sketchup::Edge)
      v1 = ent.start.position
      v2 = ent.end.position
      idx1 = (vertices_map[v1] ||= vertices_list.length; vertices_list << v1; vertices_list.length - 1)
      idx2 = (vertices_map[v2] ||= vertices_list.length; vertices_list << v2; vertices_list.length - 1)
      edges_list << [idx1, idx2]
    end
  end

  def self.get_bounding_box(sel)
    bb = Geom::BoundingBox.new
    sel.each { |ent| bb.add(ent.bounds) if ent.respond_to?(:bounds) }
    bb.empty? ? nil : bb
  end

  # -----------------------------------------------------------------
  # Import hasil proyeksi ke SketchUp (bisa dipanggil manual / auto)
  # -----------------------------------------------------------------
  def self.import_hasil(path = nil)
    unless path
      path = UI.openpanel("Pilih File Hasil Proyeksi", "", "JSON (*.json)|*.json||")
      return unless path
    end

    begin
      data = JSON.parse(File.read(path))
    rescue => e
      UI.messagebox("Gagal membaca JSON: #{e}")
      return
    end

    model = Sketchup.active_model
    model.start_operation('Import Hasil Marsekeplar', true)
    
    data['projections'].each do |side, proj|
      edges = proj['edges_2d']
      next if edges.nil? || edges.empty?
      normal_arr = data['normals'][side]
      next unless normal_arr
      normal_vec = Geom::Vector3d.new(normal_arr[0], normal_arr[1], normal_arr[2])
      origin = Geom::Point3d.new(0,0,0).offset(normal_vec, 100)

      z_local = Geom::Vector3d.new(0,0,1)
      x_local = Geom::Vector3d.new(1,0,0)
      y_local = Geom::Vector3d.new(0,1,0)

      if normal_vec.parallel?(z_local)
        basis_x = x_local
        basis_y = y_local
      else
        dot_val = z_local.dot(normal_vec)
        scaled = Geom::Vector3d.new(normal_vec.x * dot_val, normal_vec.y * dot_val, normal_vec.z * dot_val)
        proj_z = z_local - scaled
        basis_y = proj_z.length > 1e-6 ? proj_z.normalize : y_local
        basis_x = normal_vec.cross(basis_y).normalize
      end

      edges.each do |e|
        x1, y1, x2, y2 = e
        p1 = origin.offset(basis_x, x1).offset(basis_y, y1)
        p2 = origin.offset(basis_x, x2).offset(basis_y, y2)
        new_edges = model.active_entities.add_edges(p1, p2)
        new_edges.each { |edge| edge.find_faces }
      end
      
      if proj['face_colors']
        proj['face_colors'].each do |fc|
          indices = fc['indices']
          color = fc['color']
          pts = indices.map do |idx|
            p = proj['vertices_2d'][idx]
            origin.offset(basis_x, p[0]).offset(basis_y, p[1])
          end
          begin
            face = model.active_entities.add_face(pts)
            mat = model.materials.add("Marsekeplar_#{rand(9999)}")
            mat.color = Sketchup::Color.new(color[0], color[1], color[2])
            face.material = mat
          rescue
            # Face mungkin sudah ada, lewati
          end
        end
      end
    end


    model.commit_operation
    # Hapus file lock jika ada
    lock_path = File.join(Dir.tmpdir, 'marsekeplar_auto_import.lock')
    File.delete(lock_path) if File.exist?(lock_path)
    puts "Import proyeksi berhasil." unless path.nil?
    UI.messagebox("Proyeksi berhasil diimpor!") if path.nil?
  end

  # -----------------------------------------------------------------
  # Auto Import Watcher (mendeteksi file lock dari GUI Python)
  # -----------------------------------------------------------------
  def self.start_auto_import_watcher
    @auto_import_timer = UI.start_timer(2.0, true) { check_auto_import_file }
  end

  def self.check_auto_import_file
    lock_path = File.join(Dir.tmpdir, 'marsekeplar_auto_import.lock')
    result_path = File.join(Dir.tmpdir, 'marsekeplar_result.json')
    
    if File.exist?(lock_path)
      # Hapus lock agar tidak diproses dua kali
      File.delete(lock_path) rescue nil
      
      if File.exist?(result_path)
        import_hasil(result_path)  # panggil import dengan path langsung
        puts "Import otomatis berhasil dari #{result_path}"
        # Hentikan timer setelah import berhasil (opsional)
        # stop_auto_import_watcher
      end
    end
  end

  def self.stop_auto_import_watcher
    UI.stop_timer(@auto_import_timer) if @auto_import_timer
    @auto_import_timer = nil
  end
end