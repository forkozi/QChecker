# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=(78, 0, 3904, 108),
    prodvers=(78, 0, 3904, 108),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x17,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x4,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904b0',
        [StringStruct(u'CompanyName', u'NOAA NGS RSD'),
        StringStruct(u'FileDescription', u'LiPROD'),
        StringStruct(u'FileVersion', u'1, 0, 0, 0'),
        StringStruct(u'InternalName', u'LiPROD'),
        StringStruct(u'LegalCopyright', u'No copyright'),
        StringStruct(u'OriginalFilename', u'LiPROD.exe'),
        StringStruct(u'ProductName', u'LiPROD'),
        StringStruct(u'ProductVersion', u'1.0.0.0'),
        StringStruct(u'CompanyShortName', u'NOAA'),
        StringStruct(u'ProductShortName', u'LiPROD'),
        StringStruct(u'LastChange', u'42c0c8d04fdf7e2c038d517f9cf44c83559a2a58'),
        StringStruct(u'Official Build', u'1.0.0-rc2')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)