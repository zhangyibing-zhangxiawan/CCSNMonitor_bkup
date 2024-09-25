#ifndef SNEVENT_H
#define SNEVENT_H
#include "Event/EventObject.h"
#include <string>

#include "TTimeStamp.h"

using namespace std;

namespace JM{
    class SNEvent:public EventObject{
        public:
            SNEvent();
            ~SNEvent();

            //get function
            float getPromptE() const {return f_penergy;}
            float getPromptX() const {return f_pVertexX;}
            float getPromptY() const {return f_pVertexY;}
            float getPromptZ() const {return f_pVertexZ;}
            const TTimeStamp &getPromptTime() const{return m_pTime;}
            float getDelayedE() const {return f_denergy;}
            float getDelayedX() const {return f_dVertexX;}
            float getDelayedY() const {return f_dVertexY;}
            float getDelayedZ() const {return f_dVertexZ;}
            const TTimeStamp &getDelayedTime() const{return m_dTime;}

            //set function
            void setPromptE(float e){f_penergy=e;}
            void setPromptX(float x){f_pVertexX=x;}
            void setPromptY(float y){f_pVertexY=y;}
            void setPromptZ(float z){f_pVertexZ=z;}
            void setPromptTime(TTimeStamp &t){m_pTime=t;}
            void setDelayedE(float e){f_denergy=e;}
            void setDelayedX(float x){f_dVertexX=x;}
            void setDelayedY(float y){f_dVertexY=y;}
            void setDelayedZ(float z){f_dVertexZ=z;}
            void setDelayedTime(TTimeStamp &t){m_dTime=t;}

        private:
            float f_penergy;
            float f_pVertexX;
            float f_pVertexY;
            float f_pVertexZ;
            TTimeStamp m_pTime;

            float f_denergy;
            float f_dVertexX;
            float f_dVertexY;
            float f_dVertexZ;
            TTimeStamp m_dTime;

        public:
            ClassDef(SNEvent,2)
    };
}
#endif
