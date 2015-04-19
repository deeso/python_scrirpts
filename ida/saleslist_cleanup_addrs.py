#(c) Adam Pridgen adam.pridgen@thecoverofnight.com
# GPL v3
names = '''aJKJ                             0044AFDF  
aLeL                             0044D03D  
aBSn_2                           0044F23A  
aETPs_0                          0044F23F  
aLuS                             0044FF66  
aE_1                             004522D2  
aHFk                             00456519  
aGRN                             0045A48A  
aLdL_0                           0045F939  
aLdL                             0045F951  
aMK                              00461547  
aK                               0046157B  
aK_0                             00461580  
aK_1                             004639B6  
aTK                              00463A12  
aPK                              00463A17  
aMK_0                            00463A3B  
aIK                              00463A5E  
aK_2                             00463A70  
aRK                              00463A75  
a4K                              00463A7B  
aIK_0                            00463A81  
a0K                              00463AE1  
aLK                              00463AE6  
aHK                              00463AEC  
aDK                              00463AF2  
aK_3                             00463AF8  
aK_4                             00463AFE  
a@K                              00463B04  
aK_5                             00463B0A  
aK_6                             0046513F  
aK_7                             00465144  
aK_8                             0046514A  
aHK_2                            004651EF  
aHK_1                            00465209  
aAK                              004652F2  
aK_9                             00465446  
aFK                              004654A5  
aLdGxx                           00467B80  
aSk                              00479800  
aK_10                            00479846  
aHK_0                            0047984B  
aVltJHIl                         0047A6FB  
aLl                              0047C790  
aHll                             0047C795  
aMll                             0047C7B9  
aAnl                             0047D0A8  
aHanl                            0047D0AD  
aTpl                             0047D209  
aDql                             0047D20E  
aTql                             0047D232  
aQl                              0047D318  
aQl_0                            0047D31D  
aBxN                             00480D75  
aG_0                             004812F4  
aHXl                             00482350  
aVltVsE                          00483823  
aGj                              0048382E  
aDal                             0048551D  
aHdal                            0048552F  
aDbl                             00485807  
aVl                              0048595B  
a0el                             00485D0C  
aIel                             00485D1E  
aEl                              00485D41  
aIl                              00486B80  
aFl                              0048B1AE  
aFl_0                            0048B1B3  
aVh@M                            0048C896  
aWhdgn                           0048E3CB  
aSvwIN                           0048E8CC  
aJ_0                             0048E8D4  
aRxih                            0048EB4B  
aRfH                             0048ECD7  
aDJ                              00493B8B  
aGafn                            00493B90  
aGDun                            004953BC  
aRAi                             004961AB  
aRdci                            00496337  
a3@LessA                         00498A20  
aGHal                            00499226  
aGUn                             00499671  
aJH0ym                           00499B75  
aSz                              00499B7C  
aJthYm                           0049C846  
aQqbCn                           0049FEC6  
aSuvwlAak                        0049FECD  
aHfL                             004A0C09  
aHiJ                             004A2B2B  
aLeL_0                           004A4305  
aLeL_1                           004A925C  
aLeL_2                           004AD54E  
aLtNbmlji3Sr                     004AE9B3  
aBAn                             004B3BFE  
aLAn                             004B3C03  
aPqpqN                           004B3C09  
aS_6                             004B3C12  
aPN                              004B3D2C  
aSN                              004B3D36  
aRN                              004B3D40  
aIn_0                            004B3D4A  
aPin                             004B3D54  
aIn                              004B3D5E  
aHxN                             004B3D8B  
aVPN                             004B3E30  
aBSn                             004B3E90  
'''

def transform_to_code(address):
  MakeUnkn(address, 2)
  t = MakeCode(address)
  if t:  "Made x%08x into code"
  else: "Failed to make x%08x into code"
  

names = names.split("\n")
for name in names:
  print name.split()
  if not len(name.split()) > 0: continue
  address = name.split()[-1]
  try:
    address = int(address, 16)
  except:
    continue
  transform_to_code(address)

print "Finished, and hopefully it worked."
