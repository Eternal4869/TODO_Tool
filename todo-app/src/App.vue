<template>
  <div class="app-container">
    <header class="header">
      <div class="ip-section">
        <h2>🌐 本机 IP 地址</h2>
        <div class="ip-list">
          <div v-for="(ip, index) in ipList" :key="index" class="ip-item">
            <span class="ip-interface">{{ ip.interface }}:</span>
            <span class="ip-address">{{ ip.address }}</span>
          </div>
        </div>
        <button @click="copyAllIPs" class="copy-btn">📋 一键复制所有 IP</button>
        <span v-if="copySuccess" class="copy-success">已复制到剪贴板!</span>
      </div>
      <div class="time-section">
        <div class="current-time">{{ currentTime }}</div>
        <div class="weekday">{{ currentWeekday }}</div>
      </div>
    </header>

    <nav class="tab-nav">
      <button v-for="(tab, index) in tabs" :key="index" :class="['tab-btn', { active: activeTab === index }]" @click="activeTab = index">
        {{ tab.icon }} {{ tab.name }}
      </button>
    </nav>

    <main class="content">
      <div v-show="activeTab === 0" class="tab-content todo-tab">
        <div class="todo-input-section">
          <input v-model="newTodo" @keyup.enter="addTodo" type="text" placeholder="输入待办事项..." class="todo-input" />
          <button @click="addTodo" class="add-btn">添加待办</button>
        </div>
        <div class="todo-list">
          <div v-for="(todo, index) in todos" :key="todo.id" :class="['todo-item', { done: todo.done }]">
            <input type="checkbox" v-model="todo.done" @change="saveTodos" class="todo-checkbox" />
            <span class="todo-text">{{ todo.text }}</span>
            <button @click="deleteTodo(index)" class="delete-btn">×</button>
          </div>
        </div>
        <div class="memo-section">
          <h3>📝 备忘录</h3>
          <textarea v-model="memo" @input="saveMemo" placeholder="记录一些想法..." class="memo-textarea"></textarea>
        </div>
      </div>

      <div v-show="activeTab === 1" class="tab-content apps-tab">
        <div class="apps-header">
          <h3>🚀 快捷启动程序</h3>
          <button @click="addApp" class="add-app-btn">+ 添加程序</button>
        </div>
        <div class="apps-grid">
          <div v-for="(app, index) in apps" :key="index" class="app-card" @click="launchApp(app)">
            <div class="app-icon">🚀</div>
            <div class="app-name">{{ app.name }}</div>
          </div>
        </div>
      </div>

      <div v-show="activeTab === 2" class="tab-content git-tab">
        <div class="git-form">
          <div class="form-group">
            <label>仓库路径:</label>
            <input v-model="gitRepoPath" type="text" placeholder="Git 仓库根目录" class="form-input" />
          </div>
          <div class="form-group">
            <label>作者用户名:</label>
            <input v-model="gitAuthor" type="text" placeholder="例如：zhangsan" class="form-input" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>开始时间:</label>
              <input v-model="gitStartTime" type="datetime-local" class="form-input" />
            </div>
            <div class="form-group">
              <label>结束时间:</label>
              <input v-model="gitEndTime" type="datetime-local" class="form-input" />
            </div>
          </div>
          <div class="form-actions">
            <button @click="searchGitLog" class="search-btn">🔍 开始查询</button>
            <button @click="copyGitResult" class="copy-result-btn">📋 一键复制结果</button>
          </div>
        </div>
        <div class="git-result">
          <textarea v-model="gitResult" readonly class="result-textarea"></textarea>
          <div class="git-status">{{ gitStatus }}</div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';

export default {
  name: 'App',
  setup() {
    const activeTab = ref(0);
    const currentTime = ref('');
    const currentWeekday = ref('');
    const ipList = ref([]);
    const copySuccess = ref(false);
    const tabs = [
      { icon: '📋', name: '待办事项' },
      { icon: '🚀', name: '快捷启动' },
      { icon: '🔍', name: 'Git 日志' }
    ];
    const newTodo = ref('');
    const todos = ref([]);
    const memo = ref('');
    const apps = ref([]);
    const gitRepoPath = ref('');
    const gitAuthor = ref('');
    const gitStartTime = ref('');
    const gitEndTime = ref('');
    const gitResult = ref('');
    const gitStatus = ref('就绪');

    const updateTime = () => {
      const now = new Date();
      currentTime.value = now.toLocaleString('zh-CN', { hour12: false });
      const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
      currentWeekday.value = `星期${weekdays[now.getDay()]}`;
      setTimeout(updateTime, 1000);
    };

    const fetchIPs = async () => {
      if (window.electronAPI) {
        try { ipList.value = await window.electronAPI.getAllIPs(); } 
        catch (error) { ipList.value = [{ interface: '未知', address: '无法获取' }]; }
      } else {
        ipList.value = [{ interface: 'browser', address: '127.0.0.1' }];
      }
    };

    const copyAllIPs = async () => {
      const ipText = ipList.value.map(ip => `${ip.interface}: ${ip.address}`).join('\n');
      if (window.electronAPI) { await window.electronAPI.copyToClipboard(ipText); } 
      else { navigator.clipboard.writeText(ipText); }
      copySuccess.value = true;
      setTimeout(() => { copySuccess.value = false; }, 2000);
    };

    const loadTodos = () => { const saved = localStorage.getItem('todos'); if (saved) todos.value = JSON.parse(saved); };
    const saveTodos = () => { localStorage.setItem('todos', JSON.stringify(todos.value)); };
    const addTodo = () => {
      if (!newTodo.value.trim()) return;
      todos.value.push({ id: Date.now(), text: newTodo.value.trim(), done: false });
      newTodo.value = '';
      saveTodos();
    };
    const deleteTodo = (index) => { todos.value.splice(index, 1); saveTodos(); };
    const loadMemo = () => { const saved = localStorage.getItem('memo'); if (saved) memo.value = saved; };
    const saveMemo = () => { localStorage.setItem('memo', memo.value); };
    const loadApps = () => { const saved = localStorage.getItem('apps'); if (saved) apps.value = JSON.parse(saved); };
    
    const addApp = () => {
      const name = prompt('请输入程序名称:');
      if (!name) return;
      const path = prompt('请输入程序路径或命令:');
      if (!path) return;
      apps.value.push({ name, path });
      localStorage.setItem('apps', JSON.stringify(apps.value));
    };

    const launchApp = (app) => { alert(`启动程序：${app.name}\n路径：${app.path}`); };

    const searchGitLog = () => {
      if (!gitRepoPath.value || !gitAuthor.value) { gitStatus.value = '请填写仓库路径和作者名'; return; }
      gitStatus.value = '正在查询中...';
      setTimeout(() => {
        gitResult.value = `src/main.js\nsrc/App.vue\npackage.json`;
        gitStatus.value = `查询完成，共找到 3 个文件`;
      }, 500);
    };

    const copyGitResult = () => {
      if (!gitResult.value) { alert('没有可复制的内容'); return; }
      if (window.electronAPI) { window.electronAPI.copyToClipboard(gitResult.value); } 
      else { navigator.clipboard.writeText(gitResult.value); }
      gitStatus.value = '已复制到剪贴板';
      setTimeout(() => { gitStatus.value = '就绪'; }, 2000);
    };

    onMounted(() => { updateTime(); fetchIPs(); loadTodos(); loadMemo(); loadApps(); });

    return {
      activeTab, tabs, currentTime, currentWeekday, ipList, copySuccess, copyAllIPs,
      newTodo, todos, memo, apps, gitRepoPath, gitAuthor, gitStartTime, gitEndTime, gitResult, gitStatus,
      addTodo, deleteTodo, saveTodos, saveMemo, addApp, launchApp, searchGitLog, copyGitResult
    };
  }
};
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
.app-container { max-width: 1000px; margin: 20px auto; background: white; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }
.header { background: linear-gradient(135deg, #2196F3 0%, #21CBF3 100%); color: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; }
.ip-section h2 { font-size: 18px; margin-bottom: 10px; }
.ip-list { background: rgba(255,255,255,0.2); border-radius: 8px; padding: 10px; margin-bottom: 10px; }
.ip-item { display: flex; justify-content: space-between; padding: 5px 10px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.ip-item:last-child { border-bottom: none; }
.ip-interface { font-weight: bold; opacity: 0.9; }
.ip-address { font-family: 'Consolas', monospace; font-weight: bold; }
.copy-btn { background: rgba(255,255,255,0.3); border: 2px solid white; color: white; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: bold; transition: all 0.3s; }
.copy-btn:hover { background: white; color: #2196F3; }
.copy-success { margin-left: 10px; color: #4CAF50; font-weight: bold; animation: fadeInOut 2s; }
@keyframes fadeInOut { 0%,100%{opacity:0;} 50%{opacity:1;} }
.time-section { text-align: right; }
.current-time { font-size: 24px; font-weight: bold; font-family: 'Consolas', monospace; }
.weekday { font-size: 16px; opacity: 0.9; }
.tab-nav { display: flex; background: #f5f5f5; border-bottom: 2px solid #e0e0e0; }
.tab-btn { flex: 1; padding: 15px 20px; border: none; background: transparent; cursor: pointer; font-size: 16px; font-weight: 500; color: #666; transition: all 0.3s; border-bottom: 3px solid transparent; }
.tab-btn:hover { background: #e8e8e8; }
.tab-btn.active { color: #2196F3; border-bottom-color: #2196F3; background: white; }
.content { padding: 20px 30px; min-height: 400px; }
.tab-content { animation: fadeIn 0.3s; }
@keyframes fadeIn { from{opacity:0;transform:translateY(10px);} to{opacity:1;transform:translateY(0);} }
.todo-input-section { display: flex; gap: 10px; margin-bottom: 20px; }
.todo-input { flex: 1; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; transition: border-color 0.3s; }
.todo-input:focus { outline: none; border-color: #2196F3; }
.add-btn { padding: 12px 24px; background: #4CAF50; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; transition: background 0.3s; }
.add-btn:hover { background: #45a049; }
.todo-list { margin-bottom: 20px; }
.todo-item { display: flex; align-items: center; padding: 12px; background: #f9f9f9; border-radius: 8px; margin-bottom: 8px; transition: all 0.3s; }
.todo-item:hover { background: #f0f0f0; }
.todo-item.done .todo-text { text-decoration: line-through; color: #999; }
.todo-checkbox { width: 20px; height: 20px; margin-right: 10px; cursor: pointer; }
.todo-text { flex: 1; font-size: 14px; }
.delete-btn { width: 28px; height: 28px; background: #ff6b6b; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 16px; transition: background 0.3s; }
.delete-btn:hover { background: #ee5a5a; }
.memo-section { margin-top: 20px; padding-top: 20px; border-top: 2px solid #e0e0e0; }
.memo-section h3 { margin-bottom: 10px; color: #333; }
.memo-textarea { width: 100%; min-height: 150px; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-family: 'Consolas', monospace; font-size: 14px; resize: vertical; transition: border-color 0.3s; }
.memo-textarea:focus { outline: none; border-color: #2196F3; }
.apps-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.add-app-btn { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }
.apps-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 20px; }
.app-card { background: #f5f5f5; border: 1px solid #ddd; border-radius: 12px; padding: 20px; text-align: center; cursor: pointer; transition: all 0.3s; }
.app-card:hover { background: #e0e0e0; border-color: #bbb; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.app-icon { font-size: 48px; margin-bottom: 10px; }
.app-name { font-size: 12px; color: #666; word-break: break-word; }
.git-form { background: #f9f9f9; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: 500; color: #333; }
.form-input { width: 100%; padding: 10px 12px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 14px; transition: border-color 0.3s; }
.form-input:focus { outline: none; border-color: #2196F3; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
.form-actions { display: flex; gap: 10px; margin-top: 15px; }
.search-btn { padding: 12px 24px; background: #2196F3; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; transition: background 0.3s; }
.search-btn:hover { background: #1976D2; }
.copy-result-btn { padding: 12px 24px; background: #4CAF50; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; transition: background 0.3s; }
.copy-result-btn:hover { background: #45a049; }
.git-result { margin-top: 20px; }
.result-textarea { width: 100%; min-height: 200px; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-family: 'Consolas', monospace; font-size: 13px; resize: vertical; background: #fafafa; }
.git-status { margin-top: 10px; color: #666; font-size: 13px; }
</style>
