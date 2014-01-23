#include <iostream>
#include <fstream>
#include <iomanip>
#include <vector>
#include <string>
#include <math.h>

void Data(){
  //Being calculated the number of runs from luigi's file
  string line;
  ifstream luigi;
  luigi.open("data/luigi.txt");
  if(!luigi){
    cout<<"WARNING luigi.txt do not exist"<<endl;
  }
  cout<<"Reading Luigis file"<<endl;
  int l=0;
  while(!luigi.eof()){
    getline(luigi,line);
    l++;
  }
  const int runsAmmount = l-1;
  luigi.close();
  

  //Charging data from luigi's file
  ifstream luigi;
  luigi.open("data/luigi.txt");
  ifstream efftxt[runsAmmount];
  string run[runsAmmount];
  string roll[runsAmmount];
  float hvb[runsAmmount];
  float hve[runsAmmount];
  for (int n=0;n<runsAmmount;n++){
    luigi>>run[n]>>hvb[n]>>hve[n];
    cout<<n<<" "<<run[n]<<" "<<hvb[n]<<" "<<hve[n]<<endl;
  }
  luigi.close();
  
  
  //Being calculated the number of rolls from rolls.txt 
  ifstream rollslist;
  rollslist.open("data/rolls.txt");
  int l1=0;
  while(!rollslist.eof()){
    getline(rollslist,line);
    l1++;
  }
  const int rollsAmmount = l1-1;
  rollslist.close();
  
  
  //Charging data from rollyeff#a.txt files (Each file has to have the same order)
  cout<<"Opening txt files"<<endl;
  for(int n=0;n<runsAmmount;n++){
    efftxt[n].open(("data/rollYeff_"+run[n]+"a.txt").c_str());
  }
  ofstream runsData;
  float EFF[runsAmmount];
  float ERR[runsAmmount];
  float EXP[runsAmmount];
  float CLS[runsAmmount];
  bool anydifferent;
  string rollName;
  char init;
  for (int m=0;m<rollsAmmount;m++){
    for(int n=0;n<runsAmmount;n++){
      cout<<"Reading efftxt["<<n<<"]"<<endl;
      efftxt[n]>>roll[n]>>EFF[n]>>ERR[n]>>EXP[n]>>CLS[n]; //allroll[n] should be the same
      cout<<roll[n]<<" "<<EFF[n]<<" "<<ERR[n]<<" "<<EXP[n]<<" "<<CLS[n]<<endl;  
    }
    std::cout<<"Comparing strings "<<std::endl;
    anydifferent = false;
    for(int n=0;n<runsAmmount-1;n++){
      cout<<n<<" "<<roll[n]<<endl;
      if(roll[n].compare(roll[n+1])!=0){
	anydifferent = true;
	cout<<n<<endl;
      } 
    }
    if(!anydifferent){
      cout<<"All strings Match!!"<<endl;
    }
    else{
      cout<<"!!!!!!!!!!!!!!! STOP bad matching files !!!!!!!!!!!!"<<endl;
      for(int n=0;n<runsAmmount;n++ )cout<<roll[n]<<" "<<roll[0]<<endl;
      break;
      exit(0);
    }
    

    //Being saved tha data for each roll
    gSystem->mkdir("results");
    gSystem->mkdir(("results/"+roll[0]).c_str());
    runsData.open(("results/"+roll[0]+"/runsData.txt").c_str());
    cout<<"Folder created:  "<<roll[0]<<endl;
    rollName= roll[0];
    init = rollName[0];    
    for (int n=0;n<runsAmmount;n++){
      if (init=='R') 	{
	runsData<<hve[n]<<" "<<EFF[n]<<" "<<ERR[n]<<" "<<EXP[n]<<" "<<CLS[n]<<endl;
      }
      else runsData<<hvb[n]<<" "<<EFF[n]<<" "<<ERR[n]<<" "<<EXP[n]<<" "<<CLS[n]<<endl;
    }
    runsData.close();     
  }
  exit(0);
}  

   

