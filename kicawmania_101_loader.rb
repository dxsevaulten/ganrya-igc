#==============================================================================
# Nama Plugin   : kicawmania_101
# Versi         : 6.0.0
# Author        : dxse-muhammad_afgan
# Deskripsi     : my kisah, jangan pada iri ye - Marsekeplar Holographic Edition
# Kompatibilitas: SketchUp 2020 - 2026 (Make & Pro)
#==============================================================================

require 'sketchup'
require 'extensions'

module Kicawmania101
  # Arahkan langsung ke folder proyek di Google Drive
  PROJECT_DIR = "C:/Google Drive/ForeGan Tools/Edit/mykisah/kicawmania_101"
  path = File.join(PROJECT_DIR, 'reg.rb')
  
  ext = SketchupExtension.new('kicawmania_101', path)
  ext.version = '6.0.0'
  ext.creator = 'dxse-muhammad_afgan'
  ext.description = 'my kisah, jangan pada iri ye - Marsekeplar Holographic Edition'
  
  Sketchup.register_extension(ext, true)
end