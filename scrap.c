Notation is group,element (0x0010,0x0010)
 
void mapping::removeAllPrivateTags(DcmDataset &ds)
{
    Iterate tags
        if(tag.getGroup() & 1) //if the group is odd
        {
            delete
        }
}
void mapping::removeCurveData(DcmDataset &ds)
{
    Iterate tags
        
        //if group is 0x50xx
        if( (tag.getGroup() & 0xFF00) == 0x5000)
        {
            delete
        }
       
}
void mapping::cleanAllOverlays(DcmDataset &ds)
{
    iterate
        //remove overlay comments (0x60xx,0x4000)
        if( ((tag.getGroup()&0xFF00)==0x6000) && (tag.getElement()==0x4000) )
        {
            delete
        }
        //remove overlay data(0x60xx,0x3000)
        else if( ((tag.getGroup()&0xFF00)==0x6000) && (tag.getElement()==0x3000) )
        {
            delete
        }
}

Key
       File
       Look in file for existing tag value
       If found, use it
       If not found
              Generate new random string
              Write value=new random string to file
              Write to dicom
 
 
Hash
       Determining method (uid, date, time, datetime, other)
       Will need a md5 function and a crc32 function
 
bool Hash::updateDCM(DcmMetaInfo &mi, DcmDataset &ds)
{
    OFString key;
    OFCondition status;
    uint32_t crc = 0;
    const time_t ONE_DAY = 24 * 60 * 60;
    const int OFFSET = 1;
    //set up a pointer to the appropriate area
    DcmItem *di = findItem(group, mi, ds);
    
    //get the original value of whatever key we're updating
    status =di->findAndGetOFString(DcmTagKey(group, element), key);
    if(!status.good())
    {
        //printf("load failed on: %s\n", toString().c_str());
        //printf("    %s\n", status.text());
        return false;
    }
    if(std::strcmp(method.c_str(), "date") == 0)
    {
        //first, get subjid - 10,10 in the ds
        OFString seed;
        MD5 md5;
        struct tm tm;
        char buf[9];
        ds.findAndGetOFString(DCM_PatientName, seed);
        //lots of funky stuff going on, strdup converts const char* to a char*, * dereferences so I can do binary ops
        //only keep bits 0x0000 1010 (0 to 10), which we'll make into +1 to 11 days
        crc = (*md5.digestString(strdup(seed.c_str())) & 0x0A);
        //adjust date - convert key to a date
        //need to clear this or you get underfined results
        memset(&tm, 0, sizeof(struct tm));
        strptime(key.c_str(), "%Y%m%d", &tm);
        time_t newSecs = mktime(&tm) + (((int)crc + OFFSET) * ONE_DAY);
//        const struct tm *newDay = localtime(&newSecs);
//        strftime(buf, 9, "%Y%m%d", newDay);
        strftime(buf, 9, "%Y%m%d", localtime(&newSecs));
        status = di->putAndInsertString(DcmTagKey(group,element), buf);
//TODO - special case, birthdate?, if over 90
    }
    else if(std::strcmp(method.c_str(), "uid") == 0)
    {
        //calculate a new uid
        //massive modify of dcmGenerateUniqueIdentifier
        char buf[128]; /* be very safe */
        char uid[100];
        uid[0] = '\0'; /* initialise */
        /* On 64-bit Linux, the "32-bit identifier" returned by gethostid() is
         sign-extended to a 64-bit long, so we need to blank the upper 32 bits */
        long hostIdentifier = OFstatic_cast(unsigned long, gethostid() & 0xffffffff);
        addUIDComponent(uid, SITE_INSTANCE_UID_ROOT);
        sprintf(buf, ".%lu", hostIdentifier);
        addUIDComponent(uid, buf);
        //use the initial UID to seed the rest of the new one
        //crc = crc32c(crc, const unsigned char *buf, size_t len);
        crc = crc32c(crc, key.c_str(), key.length());
        sprintf(buf, ".%u", crc);
        addUIDComponent(uid, buf);
//printf("orig:%s   new:%s\n", key.c_str(), uid);
        //write back the new UID
        status = di->putAndInsertString(DcmTagKey(group,element), uid);
    }
    
    else if(std::strcmp(method.c_str(), "time") == 0)
    {
        char *uid = strdup("120000.000000");
        //printf("orig:%s   new:%s\n", key.c_str(), uid);
        status = di->putAndInsertString(DcmTagKey(group,element), uid);
    }
    else if(std::strcmp(method.c_str(), "datetime") == 0)
    {
        //see "date" for general notes
        OFString seed;
        MD5 md5;
        struct tm tm;
        char buf[13];
        ds.findAndGetOFString(DCM_PatientID, seed);
        crc = (*md5.digestString(strdup(seed.c_str())) & 0x0A);
        memset(&tm, 0, sizeof(struct tm));
        std::string s(key.c_str());
        std::string temp = splitOnChar(s, '.');
        strptime(temp.c_str(), "%Y%m%d%H%M%S", &tm);
        tm.tm_hour = 12;
        tm.tm_min = 0;
        tm.tm_sec = 0;
        time_t newSecs = mktime(&tm) + (((int)crc + OFFSET) * ONE_DAY);
        strftime(buf, 13, "%Y%m%d%H%M%S", localtime(&newSecs));
        status = di->putAndInsertString(DcmTagKey(group,element), buf);
    }
    else if(std::strcmp(method.c_str(), "other") == 0)
    {
        //just a md5 on the input string and then write back
        MD5 md5;
        char *uid = md5.digestString(strdup(key.c_str()));
        //printf("orig:%s   new:%s\n", key.c_str(), uid);
        status = di->putAndInsertString(DcmTagKey(group,element), uid);
    }
    else
    {
//TODO
        //not sure yet, might be the same as none
        //hmmm, maybe, it does a crc with the method as the start value?
        //crc = crc32c(crc, key.c_str(), key.length());
    }
    
    //should be able to return status.good();
    return status.good();
}
 