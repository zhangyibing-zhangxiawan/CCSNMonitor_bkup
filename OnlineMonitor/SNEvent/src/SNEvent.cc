#include "Event/SNEvent.h"

ClassImp(JM::SNEvent);
namespace JM{
    SNEvent::SNEvent(){
        f_penergy=0;
        f_pVertexX=0;
        f_pVertexY=0;
        f_pVertexZ=0;
        m_pTime=TTimeStamp(0, 0);

        f_denergy=0;
        f_dVertexX=0;
        f_dVertexY=0;
        f_dVertexZ=0;
        m_dTime=TTimeStamp(0, 0);
    }

    SNEvent::~SNEvent(){
    }

}
