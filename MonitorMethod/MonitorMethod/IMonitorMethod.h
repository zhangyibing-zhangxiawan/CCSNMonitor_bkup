#ifndef IMONITORMETHOD_H
#define IMONITORMETHOD_H
#include <deque>
#include "TTimeStamp.h"

class IMonitorMethod{
    public:
        IMonitorMethod();
        virtual ~IMonitorMethod();

        virtual bool init() = 0;
        virtual bool fina() = 0;
        virtual std::deque<TTimeStamp> findAlert(const std::deque<TTimeStamp>&) = 0;
    private:
};
#endif
