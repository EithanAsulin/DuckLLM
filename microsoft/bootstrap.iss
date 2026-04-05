[Setup]
AppName=DuckLLM Downloader
AppVersion=1.0
DefaultDirName={tmp}
DisableDirPage=yes
CreateAppDir=no
OutputBaseFilename=DuckLLM_Bootstrap

[Code]
var
  DownloadPage: TDownloadWizardPage;

procedure InitializeWizard;
begin
  DownloadPage := CreateDownloadPage('Downloading DuckLLM', 'Please wait while we fetch the latest installer...', nil);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  if CurPageID = wpReady then
  begin
    DownloadPage.Clear;
    DownloadPage.Add('https://huggingface.co/datasets/DuckLLM/DuckLLM-Microsoft-Store/resolve/main/DuckLLM_Installer.exe', 'DuckLLM_Installer.exe', '');
    
    DownloadPage.Show;
    try
      try
        DownloadPage.Download;
        Result := True;
      except
        MsgBox('Download failed: ' + GetExceptionMessage, mbError, MB_OK);
        Result := False;
      end;
    finally
      DownloadPage.Hide;
    end;
  end else
    Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    Log('Running the downloaded installer...');
    
    if not Exec(ExpandConstant('{tmp}\DuckLLM_Installer.exe'), '', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
    begin
      MsgBox('Failed to run the installer. Error code: ' + IntToStr(ResultCode), mbError, MB_OK);
    end;
  end;
end;
