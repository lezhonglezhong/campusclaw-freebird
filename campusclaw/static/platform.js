(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const auth = window.CampusClawAuth;
  let templates = [], skills = [], apps = [], defaultTemplate = '', user;
  const jsonOptions = (method, body) => ({method, headers: {'Content-Type':'application/json'}, body:JSON.stringify(body)});
  async function api(path, options) {
    const response = await auth.request(path, options);
    const data = response.status === 204 ? {} : await response.json();
    if (!response.ok) {
      const error = new Error(data.error || 'request_failed');
      error.data = data;
      throw error;
    }
    return data;
  }
  function message(id, text) { $(id).textContent = text; }
  function options(select, items, initial, selected) {
    select.replaceChildren(new Option(initial, ''));
    for (const item of items) select.add(new Option(item.name, String(item.id)));
    if ([...select.options].some(o => o.value === selected)) select.value = selected;
  }
  function preview() {
    const template = templates.find(t => String(t.id) === $('#template-id').value);
    const values = {input:$('#run-input').value, audience:$('#audience').value};
    message('#template-preview', (template ? template.content : defaultTemplate).replace(/\{\{(input|audience)\}\}/g, (_, key) => values[key]));
    const skill = skills.find(s => s.id === $('#skill-id').value);
    message('#skill-preview', skill ? JSON.stringify(skill.manifest, null, 2) : '未选择技能');
    $('#delete-skill').disabled = !skill || skill.builtin;
    const app = apps.find(a => a.id === $('#app-id').value);
    message('#app-description', app ? app.description : '');
  }
  async function loadTemplates() {
    templates = (await api('/api/platform/templates')).templates;
    options($('#template-id'), templates, '应用默认模板', $('#template-id').value);
    options($('#edit-template-id'), templates, '新建模板', $('#edit-template-id').value);
    preview();
  }
  async function loadSkills() {
    skills = (await api('/api/platform/skills')).skills;
    options($('#skill-id'), skills.map(s => ({id:s.id, name:(s.builtin ? '内置 · ' : '班级 · ')+s.manifest.name})), '不使用技能', $('#skill-id').value);
    preview();
  }
  async function loadTools() {
    const data = await api('/api/platform/tools');
    const target = $('#tool-choices'); target.replaceChildren();
    for (const item of data.tools) {
      const label = document.createElement('label');label.className = 'checkbox';
      const checkbox = document.createElement('input');checkbox.type = 'checkbox';checkbox.value = item.definition.function.name;
      label.append(checkbox, document.createTextNode(item.connector_id+' · '+item.definition.function.description));
      target.append(label);
    }
    if (!data.tools.length) target.textContent = '暂无可用工具，请教师启用连接。';
    if (data.errors.length) {
      const warning = document.createElement('p'); warning.textContent = '部分连接暂不可用：'+data.errors.map(e => e.connector_id).join('、');target.append(warning);
    }
  }
  async function loadConnectors() {
    const data = await api('/api/platform/connectors');
    const controls = $('#connector-controls');controls.replaceChildren();
    for (const item of data.connectors) {
      const button = document.createElement('button');button.type = 'button';
      button.textContent = (item.enabled ? '停用 ' : '启用 ')+item.label+' ('+item.type.toUpperCase()+')';
      button.addEventListener('click', async () => {
        button.disabled = true;
        try {
          await api('/api/platform/connectors/'+encodeURIComponent(item.id), jsonOptions('PUT',{enabled:!item.enabled}));
          await loadConnectors(); await loadTools();message('#connector-status','连接状态已更新。');
        } catch { message('#connector-status','连接更新失败，请重试。');button.disabled = false; }
      });controls.append(button);
    }
    if (!data.connectors.length) controls.textContent = '部署尚未配置外部服务。';
  }
  async function showRun(id) {
    const run = await api('/api/platform/runs/'+id);
    message('#run-trace', JSON.stringify(run, null, 2));
    const result = run.trace.result;
    $('#run-answer').hidden = !result;
    message('#run-answer', result ? result.answer : '');
    $('#run-citations').replaceChildren();
    for (const citation of (result ? result.citations : [])) {
      const li = document.createElement('li'); const link = document.createElement('a');
      link.href = '/materials?material_id='+encodeURIComponent(citation.material_id);
      link.textContent = '['+citation.number+'] '+citation.material_title;
      li.append(link);$('#run-citations').append(li);
    }
    message('#run-status', run.status === 'completed' ? '执行完成。' : '执行失败，请查看记录或稍后重试。');
  }
  async function loadRuns() {
    const data = await api('/api/platform/runs'); $('#run-history').replaceChildren();
    for (const run of data.runs) {
      const li = document.createElement('li'), button = document.createElement('button');button.type = 'button';
      const app = apps.find(a => a.id === run.app_id);
      button.textContent = '#'+run.id+' '+(app ? app.name : run.app_id)+' · '+(run.status === 'completed' ? '完成' : run.status === 'failed' ? '失败' : '运行中');
      button.addEventListener('click', () => showRun(run.id).catch(() => message('#run-status','记录加载失败。')));
      li.append(button);$('#run-history').append(li);
    }
  }
  $('#run-form').addEventListener('input', preview);
  $('#run-form').addEventListener('change', preview);
  $('#run-form').addEventListener('submit', async event => {
    event.preventDefault();$('#run-button').disabled = true;message('#run-status','正在执行，请稍候…');
    $('#run-answer').hidden = true;$('#run-citations').replaceChildren();message('#run-trace','正在执行…');
    const body = {app_id:$('#app-id').value, input:$('#run-input').value, audience:$('#audience').value,
      template_id:$('#template-id').value ? Number($('#template-id').value) : null,
      skill_id:$('#skill-id').value || null, use_knowledge:$('#use-knowledge').checked,
      tools:[...$('#tool-choices').querySelectorAll('input:checked')].map(c => c.value)};
    try {const result = await api('/api/platform/runs',jsonOptions('POST',body));await showRun(result.run_id);}
    catch (error) {
      if (error.data && error.data.run_id) await showRun(error.data.run_id).catch(() => {});
      message('#run-status','执行失败：请检查输入与服务状态，详细步骤见执行记录。');
    } finally {$('#run-button').disabled = false;await loadRuns().catch(() => {});}
  });
  $('#edit-template-id').addEventListener('change', () => {
    const item = templates.find(t => String(t.id) === $('#edit-template-id').value);
    $('#template-name').value = item ? item.name : '';$('#template-content').value = item ? item.content : '';
    $('#delete-template').disabled = !item;
  });
  $('#template-form').addEventListener('submit', async event => {
    event.preventDefault(); const id = $('#edit-template-id').value;
    try {
      const data = await api('/api/platform/templates'+(id ? '/'+id : ''), jsonOptions(id ? 'PUT' : 'POST',{name:$('#template-name').value,content:$('#template-content').value}));
      await loadTemplates();$('#template-id').value = String(data.template.id);$('#edit-template-id').value = String(data.template.id);
      $('#delete-template').disabled = false;preview();message('#template-status','模板已保存并选中。');
    } catch { message('#template-status','保存失败，请检查长度及变量名称。'); }
  });
  $('#delete-template').addEventListener('click', async () => {
    const id = $('#edit-template-id').value;if (!id) return;
    try {await api('/api/platform/templates/'+id,{method:'DELETE'});await loadTemplates();$('#edit-template-id').dispatchEvent(new Event('change'));message('#template-status','模板已删除。');}
    catch {message('#template-status','删除失败。');}
  });
  $('#skill-form').addEventListener('submit', async event => {
    event.preventDefault();const data = new FormData();data.append('file',$('#skill-file').files[0]);
    try {const result = await api('/api/platform/skills',{method:'POST',body:data});await loadSkills();$('#skill-id').value = result.skill.id;preview();message('#skill-status','技能已上传并选中。');}
    catch {message('#skill-status','上传失败：请使用有效的 JSON 技能文件（最多 16 KiB）。');}
  });
  $('#delete-skill').addEventListener('click', async () => {
    const id = $('#skill-id').value;if (!id.startsWith('uploaded:')) return;
    try {await api('/api/platform/skills/'+id.slice(9),{method:'DELETE'});await loadSkills();message('#skill-status','技能已删除。');}
    catch {message('#skill-status','删除失败。');}
  });
  $('#platform-logout').addEventListener('click', () => {auth.clearToken();window.location.replace('/login');});
  async function initialize() {
    user = (await api('/api/me')).user;
    message('#platform-user',user.class_name+' · '+user.account+' · '+(user.role === 'teacher' ? '教师' : '学生'));
    const catalog = await api('/api/platform/apps');apps = catalog.apps;defaultTemplate = catalog.default_template;
    $('#app-id').replaceChildren(...apps.map(a => new Option(a.name,a.id)));
    for (const id of ['#template-management','#skill-management','#connector-management']) $(id).hidden = user.role !== 'teacher';
    await Promise.all([loadTemplates(),loadSkills(),loadTools(),loadRuns(),user.role === 'teacher' ? loadConnectors() : Promise.resolve()]);
    preview();
  }
  initialize().catch(() => message('#platform-status','加载失败，请刷新页面或重新登录。'));
})();
