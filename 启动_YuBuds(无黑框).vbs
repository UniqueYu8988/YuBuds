Set WshShell = CreateObject("WScript.Shell")
' 获取当前脚本所在目录
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
' 切换到该目录并启动 Python 运行 main.py，0 表示隐藏窗口，False 表示不等待结束
WshShell.Run "cmd /c cd /d """ & strPath & """ && python main.py", 0, False
