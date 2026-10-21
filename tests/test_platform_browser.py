"""Real Chromium acceptance against local Flask and independent HTTP/MCP service."""
import json
import os
from pathlib import Path
import threading
from dataclasses import replace
import pytest
from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server
from tests.test_platform_catalog import app
from campusclaw.demo_tools import app as demo_app, demo_connectors
from campusclaw.platform_tools import configured_tools
from campusclaw.platform_chat import PlatformChat


@pytest.fixture
def site(app):
    demo=make_server('127.0.0.1',0,demo_app,threaded=True)
    demo_thread=threading.Thread(target=demo.serve_forever,daemon=True);demo_thread.start()
    app.config['PLATFORM_CONNECTORS']=configured_tools(demo_connectors(f'http://127.0.0.1:{demo.server_port}'))
    calls=[]
    settings=replace(app.config['GATEWAY_SETTINGS'],chat_base_url='https://synthetic/v1',chat_api_key='test')
    def transport(url,payload,*_):
        calls.append(payload)
        if payload.get('tools') and payload['messages'][-1]['role']!='tool':
            message={'role':'assistant','content':None,'tool_calls':[{'id':'call-'+str(len(calls)),'type':'function','function':{
                'name':payload['tools'][0]['function']['name'],'arguments':'{"a":6,"b":7,"operation":"multiply"}'}}]}
        else:message={'role':'assistant','content':'已完成合成内容；计算结果为42。'}
        return {'choices':[{'message':message}]}
    app.extensions['platform_chat']=PlatformChat(settings,transport)
    server=make_server('127.0.0.1',0,app,threaded=True)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    yield f'http://127.0.0.1:{server.server_port}',calls
    server.shutdown();server.server_close();thread.join();demo.shutdown();demo.server_close();demo_thread.join()


def login(page,base,account):
    page.goto(base+'/login')
    page.locator('input[name="account"]').fill(account)
    page.locator('input[name="password"]').fill(account+'-password')
    page.locator('button[type="submit"]').click()
    page.wait_for_url('**/materials')
    page.get_by_role('link',name='AI 应用工作台').click()
    expect(page.locator('#app-id option')).to_have_count(3)


def test_teacher_browser_template_skill_tools_execution_and_trace(site,tmp_path):
    base,calls=site
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1000})
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        login(page,base,'teacher-a')
        page.locator('#template-name').fill('浏览器模板')
        page.locator('#template-content').fill('面向{{audience}}改写{{input}}')
        page.get_by_role('button',name='保存模板',exact=True).click()
        expect(page.locator('#template-status')).to_contain_text('已保存')
        page.locator('#template-name').fill('更新后的模板')
        page.get_by_role('button',name='保存模板',exact=True).click()
        expect(page.locator('#template-id option:checked')).to_have_text('更新后的模板')
        page.locator('#run-input').fill('请计算6乘7并解释思路')
        expect(page.locator('#template-preview')).to_contain_text('面向学生改写请计算6乘7')
        page.locator('#skill-file').set_input_files(str(Path('campusclaw/static/example-skill.json').resolve()))
        page.get_by_role('button',name='上传技能',exact=True).click()
        expect(page.locator('#skill-status')).to_contain_text('已上传')
        expect(page.locator('#skill-id option:checked')).to_contain_text('三点总结')
        page.get_by_role('button',name='启用 演示 MCP 计算器 (MCP)',exact=True).click()
        expect(page.locator('#tool-choices input')).to_have_count(1)
        page.locator('#tool-choices input').check()
        page.get_by_role('button',name='运行应用',exact=True).click()
        expect(page.locator('#run-status')).to_have_text('执行完成。',timeout=15000)
        expect(page.locator('#run-answer')).to_contain_text('42')
        expect(page.locator('#run-trace')).to_contain_text('tool_calls')
        expect(page.locator('#run-trace')).to_contain_text('完整Skill清单')
        assert len(calls)==4  # two skill stages, each tool request + final answer
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        screenshot_dir=os.environ.get('PLATFORM_SCREENSHOT_DIR')
        if screenshot_dir:
            Path(screenshot_dir).mkdir(parents=True,exist_ok=True)
            page.screenshot(path=str(Path(screenshot_dir)/'workspace.png'),full_page=True)
        page.locator('#delete-skill').click()
        expect(page.locator('#skill-status')).to_contain_text('已删除')
        page.locator('#delete-template').click()
        expect(page.locator('#template-status')).to_contain_text('已删除')
        assert errors==[]
        browser.close()


def test_anonymous_redirect_and_student_readonly_mobile_workspace(site):
    base,_=site
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':390,'height':844})
        page.goto(base+'/apps');page.wait_for_url('**/login')
        login(page,base,'student-a')
        expect(page.locator('#template-management')).to_be_hidden()
        expect(page.locator('#skill-management')).to_be_hidden()
        expect(page.locator('#connector-management')).to_be_hidden()
        page.locator('#app-id').select_option('exercises')
        page.locator('#run-input').fill('分数加法')
        page.get_by_role('button',name='运行应用',exact=True).click()
        expect(page.locator('#run-status')).to_have_text('执行完成。')
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        page.get_by_role('button',name='退出登录',exact=True).click()
        page.wait_for_url('**/login')
        assert page.evaluate('sessionStorage.getItem("campusclaw.access_token")') is None
        browser.close()
