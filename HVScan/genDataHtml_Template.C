#include <iostream>
#include <fstream>
#include <iomanip>
#include <vector>
#include <string>
#include <math.h>

void genDataHtml(){
  //Being charged the list of rolls
  ifstream rolls;
  rolls.open("data/-place-.txt");
  ofstream dataHtml;
  dataHtml.open("results/dataHtml-place-.txt");
  string rollName;
  string line;
  ifstream itmp;
  rolls>>rollName;
  //Being generated the file with the information of every roll in the list
  while (!rolls.eof()){
    itmp.open(("results/"+rollName+"/fitData.txt").c_str());
    cout<<rollName<<endl;
    getline(itmp,line);
    dataHtml<<rollName<<" "<<line<<endl;
    itmp.close();
    rolls>>rollName;
  }
  rolls.close();
  dataHtml.close();
  exit(0);
}
