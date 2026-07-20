@echo off
chcp 65001 >nul
title Claire Local Refresh Server
cd /d "C:\Users\limiao.CMIT\OneDrive - 神州网信技术有限公司\06 乾元\Claire_assistant"
echo ============================================================
echo  Claire 本地刷新服务
echo  监听 http://127.0.0.1:8787
echo  让 GitHub Pages 表单的刷新按钮可以触发本机的 Claude
echo  关闭此窗口即可停止服务
echo ============================================================
python local_refresh_server.py
pause
