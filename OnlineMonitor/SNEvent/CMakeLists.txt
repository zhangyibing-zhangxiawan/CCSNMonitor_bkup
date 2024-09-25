EDM(SNEvent
        src/SNEventBook.cc
    NOXOD
    FILES
        SNEvent
        SNHeader
    )
#get_target_property(hdrs offline::BaseEvent INTERFACE_INCLUDE_DIRECTORIES)
#foreach(d ${hdrs})
#    message("--------- ${d}")
#    include_directories(${d})
#endforeach()
#target_include_directories(SNEvent PUBLIC offline::EDMUtil offline::BaseEvent)
#get_directory_property(incdirs INCLUDE_DIRECTORIES)
#foreach( d ${incdirs})
#    message("======== ${d}")
#endforeach()
#get_target_property(hdrs offline::BaseEvent INTERFACE_INCLUDE_DIRECTORIES)
#foreach(d ${hdrs})
#    message("--------- ${d}")
#endforeach()
