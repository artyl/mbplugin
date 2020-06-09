//+---------------------------------------------------------------------------
//
//  dllplugin.c - DLL plugin - dynamically linked part
//  Author - ArtyLa

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>

#define MAXBUF 10000
#define BUFFSZ 4096

// from https://stackoverflow.com/questions/8487986/file-macro-shows-full-path
#define __FILENAME__ (strrchr(__FILE__, '/') ? strrchr(__FILE__, '/') + 1 : __FILE__)

//from  https://stackoverflow.com/questions/35969730/how-to-read-output-from-cmd-exe-using-createprocess-and-createpipe
int callInterpreter(char *request, char *dllname, char *response, int responseSize)
{
	char dllpath[MAX_PATH] = {0}; 
	char mbpluginpath[MAX_PATH] = {0}; 
	strncpy(dllpath, __FILE__, strlen(__FILE__)-strlen(__FILENAME__)-1); // get path 
	strncpy(mbpluginpath, dllpath, strlen(dllpath)-strlen(strrchr(dllpath, '/'))); // get path/..
	for(int i=0;mbpluginpath[i]!='\0';i++){mbpluginpath[i] = mbpluginpath[i]=='/' ? '\\' : mbpluginpath[i];} // replace '/' -> '\\'
	// Set RequestVariable environment
	char RequestVariable[MAXBUF]={0};
	snprintf(RequestVariable, MAXBUF, "RequestVariable=%s", request);
	putenv(RequestVariable);
	
	// Call cmdplugin
    BOOL ok = TRUE;
    HANDLE hStdInPipeRead = NULL;
    HANDLE hStdInPipeWrite = NULL;
    HANDLE hStdOutPipeRead = NULL;
    HANDLE hStdOutPipeWrite = NULL;

    // Create two pipes.
    SECURITY_ATTRIBUTES sa = { sizeof(SECURITY_ATTRIBUTES), NULL, TRUE };
    ok = CreatePipe(&hStdInPipeRead, &hStdInPipeWrite, &sa, 0);
    if (ok == FALSE) return -1;
    ok = CreatePipe(&hStdOutPipeRead, &hStdOutPipeWrite, &sa, 0);
    if (ok == FALSE) return -1;

    // Create the process.
    STARTUPINFO si = { };
    si.cb = sizeof(STARTUPINFO);
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdError = hStdOutPipeWrite;
    si.hStdOutput = hStdOutPipeWrite;
    si.hStdInput = hStdInPipeRead;
    PROCESS_INFORMATION pi = { };

	char lpCommandLine[MAXBUF] = {0};
	snprintf(lpCommandLine, MAXBUF, "%s\\plugin\\mbplugin.bat %s", mbpluginpath, dllname);
    ok = CreateProcess(NULL, lpCommandLine, NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi);
	
    if (ok == FALSE) return -1;

    // Close pipes we do not need.
    CloseHandle(hStdOutPipeWrite);
    CloseHandle(hStdInPipeRead);

    // The main loop for reading output from the DIR command.
    char buf[1024 + 1] = {0};
    DWORD dwRead = 0;
    DWORD dwAvail = 0;
    ok = ReadFile(hStdOutPipeRead, buf, 1024, &dwRead, NULL);
	snprintf(response, responseSize, ""); // zeroing string
    while (ok == TRUE)
    {
        buf[dwRead] = '\0';
		if(strlen(response)+strlen(buf)<responseSize){
			strcat(response, buf);
		} else { break; }		
        ok = ReadFile(hStdOutPipeRead, buf, 1024, &dwRead, NULL);
    }

    // Clean up and exit.
    CloseHandle(hStdOutPipeRead);
    CloseHandle(hStdInPipeWrite);
    DWORD dwExitCode = 0;
    GetExitCodeProcess(pi.hProcess, &dwExitCode);
    return dwExitCode;
} // callInterpreter

__declspec(dllexport) void IssaPlugin (char *cmd, char *request, char *result, long resultsize)
{
	char buf[MAXBUF]={0};
	char resultInfo[MAXBUF]={0};
	char dllname[MAX_PATH]={0}; 
	strncpy(dllname, __FILENAME__ , strlen(__FILENAME__)-2);
	snprintf(resultInfo, MAXBUF, "<IssaPlugin>\n<Operator>DLL %s</Operator>\n<ShortName>%s</ShortName>\n<Author>ArtyLa</Author>\n<Version>%s</Version>\n</IssaPlugin>", dllname, dllname, __DATE__);
	if(strcmp(cmd,"Info")==0){
		snprintf(result, resultsize, "%s" ,resultInfo); // cmd==Info
	}
	else if (strcmp(cmd,"Execute")==0){
		char resultExecute[MAXBUF];
		callInterpreter(request, dllname, resultExecute, MAXBUF);
		snprintf(result, resultsize, "%s" ,resultExecute); // cmd==Execute
	}
	else {
		snprintf(result, resultsize, "Unknown command" ); // cmd==Execute
	}
	
	//DEBUG PRINT
	//snprintf(buf, MAXBUF, "cmd=%s\nrequest=%s\nresult=%s\n%s", cmd, request, result, dllname);
	//MessageBox (0, buf, "PLUGIN", MB_ICONINFORMATION);	
}
