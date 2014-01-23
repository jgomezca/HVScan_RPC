#include <iostream>
#include <fstream>
#include <iomanip>
#include <vector>
#include <string>
#include <math.h>

void wpChannel(){
  //Being read the working point per channel
  string line;
  ifstream rollslist;
  rollslist.open("data/wpChannel.txt");
  string rollName;
  string wpDef;
  rollslist>>rollName>>wpDef;
  cout<<rollName<<wpDef;
  int i=0;
  ofstream wpChannel;
  //Being generated the file with working point per roll according with the working point per channel
  while((!rollslist.eof())&&(i<2145)){
    i++;
    wpChannel.open(("results/"+rollName+"/wpChannel.txt").c_str());
    wpChannel<<wpDef;
    wpChannel.close();
    rollslist>>rollName>>wpDef;
    cout<<rollName<<wpDef<<endl;
  }
  exit(0);
}  

   

