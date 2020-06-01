//+---------------------------------------------------------------------------
//
//  test_dllplugin.c - Demo call dllplugin.c
//

#include <windows.h>
//#include <stdlib.h>

__declspec(dllexport) void IssaPlugin (char *cmd, char *request,char *result, long resultsize);

char* RequestInfo()
{
	char cmd[]="Info"; //CMD Info Execute
	char request[]=""; // Request
	char result[4096]; //Buffer ="Str3333"; 0000000000
	long resultsize=0x0800; //Buffer size
	char buf1[0x10];  // Ќадо разобратьс€, сюда что-то прилетает
	
	MessageBox (0, cmd, "Header IssaPlugin3", MB_ICONINFORMATION);
	IssaPlugin(cmd, request, result, resultsize);
    return result;
}

char* RequestBalance()
{
	char cmd[]="Execute"; //CMD Info Execute
	char request[]="<?xml version=\"1.0\" encoding=\"windows-1251\" ?>\n<Request>\n<ParentWindow>007F09DA</ParentWindow>\n<Login>p_test_1234567</Login>\n<Password>pass1234</Password>\n</Request>"; // Request
	char result[4096]; //Buffer 
	long resultsize=4096; //Buffer size
	char buf1[0x10];  // Ќадо разобратьс€, сюда что-то прилетает

	MessageBox (0, cmd, "Header IssaPlugin3", MB_ICONINFORMATION);
	IssaPlugin(cmd, request, result, resultsize);
    return result;
}



int WINAPI WinMain(HINSTANCE hInstance,HINSTANCE hPrevInstance,LPSTR lpCmdLine,int nCmdShow)
{
	char* result;
	result=RequestInfo();
	MessageBox (0, result, "Responce Info IssaPlugin3", MB_ICONINFORMATION);
	result=RequestBalance();
	MessageBox (0, result, "Responce Balance IssaPlugin3", MB_ICONINFORMATION);
    return 0;
}
