<template>
  <div v-if="!user" class="login-page">
    <div class="login-card">
      <div class="brand" style="color: #1f2937; border-bottom: 0; padding: 0 0 14px">
        <div class="brand-mark">粤</div>
        <div>
          <div class="login-title">粤教服务智能工作台</div>
          <div class="login-sub">基于 Dify 的国际教育智能服务平台</div>
        </div>
      </div>
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="账号">
          <el-input v-model="loginForm.username" placeholder="admin / employee / student / customer" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="loginForm.password" type="password" show-password />
        </el-form-item>
        <el-button type="primary" style="width: 100%" :loading="loading.login" @click="handleLogin">
          <el-icon><Key /></el-icon>
          登录系统
        </el-button>
      </el-form>
      <div class="quick-row" style="margin-top: 14px">
        <el-button size="small" @click="quickLogin('admin')">管理员</el-button>
        <el-button size="small" @click="quickLogin('employee')">员工</el-button>
        <el-button size="small" @click="quickLogin('student')">学生</el-button>
        <el-button size="small" @click="quickLogin('customer')">客户</el-button>
      </div>
    </div>
  </div>

  <div v-else class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">粤</div>
        <div>
          <div class="brand-title">国际教育智能平台</div>
          <div class="brand-sub">Dify + FastAPI + MySQL</div>
        </div>
      </div>

      <nav class="nav-list">
        <button
          v-for="item in visibleNav"
          :key="item.key"
          class="nav-item"
          :class="{ active: activePage === item.key }"
          @click="activePage = item.key"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <div class="sidebar-foot">
        <div>{{ user.real_name }} / {{ roleLabel }}</div>
        <div>{{ user.department || '暂无部门' }}</div>
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <div>
          <div class="page-title">{{ currentNav?.label }}</div>
          <div class="page-desc">{{ currentNav?.desc }}</div>
        </div>
        <div class="table-actions">
          <el-tag type="success" effect="plain">{{ health.database ? '数据库正常' : '数据库未连接' }}</el-tag>
          <el-button @click="refreshAll">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button type="danger" plain @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            退出
          </el-button>
        </div>
      </header>

      <section class="content">
        <template v-if="activePage === 'dashboard'">
          <div class="grid three">
            <div class="panel metric">
              <div class="metric-label">意向客户</div>
              <div class="metric-value">{{ dashboard.metrics?.leads || 0 }}</div>
              <div class="metric-note">含新加坡与德国方向线索</div>
            </div>
            <div class="panel metric">
              <div class="metric-label">待处理投诉</div>
              <div class="metric-value">{{ dashboard.metrics?.pending_feedback || 0 }}</div>
              <div class="metric-note">售后服务响应重点</div>
            </div>
            <div class="panel metric">
              <div class="metric-label">心理预警</div>
              <div class="metric-value">{{ dashboard.metrics?.psych_alerts || 0 }}</div>
              <div class="metric-note">需顾问主动关怀</div>
            </div>
          </div>

          <div class="grid two" style="margin-top: 16px">
            <div class="panel">
              <div class="panel-title"><el-icon><TrendCharts /></el-icon>客户项目分布</div>
              <div v-for="item in dashboard.project_distribution || []" :key="item.name" class="score-row">
                <span>{{ item.name }}</span>
                <el-progress :percentage="Math.min(100, item.value * 35)" :show-text="false" />
                <strong>{{ item.value }}</strong>
              </div>
            </div>
            <div class="panel">
              <div class="panel-title"><el-icon><Checked /></el-icon>20 分钟演示主线</div>
              <el-steps direction="vertical" :active="5" finish-status="success">
                <el-step title="客户咨询" description="询问新加坡或德国项目" />
                <el-step title="客户研判" description="上传资料并生成 A/B/C 画像" />
                <el-step title="CRM 跟进" description="保存线索并更新状态" />
                <el-step title="学生服务" description="提交请假或投诉并处理" />
                <el-step title="智能报告" description="生成客户经营或投诉周报" />
              </el-steps>
            </div>
          </div>
        </template>

        <template v-if="activePage === 'customerChat'">
          <div class="grid two">
            <div class="panel chat-box">
              <div class="panel-title"><el-icon><ChatDotRound /></el-icon>客服咨询 Agent</div>
              <div class="messages">
                <div v-for="(msg, index) in customerMessages" :key="index" class="message" :class="msg.role">
                  <div class="bubble">{{ msg.content }}</div>
                </div>
              </div>
              <div class="quick-row">
                <el-button size="small" @click="askCustomer('新加坡 2+2 国际本科班多少钱？')">新加坡费用</el-button>
                <el-button size="small" @click="askCustomer('德国双元制项目适合什么人？')">德国项目</el-button>
                <el-button size="small" @click="askCustomer('公司的联系方式是什么？')">公司信息</el-button>
              </div>
              <el-input v-model="customerInput" placeholder="输入客户问题" @keyup.enter="sendCustomer">
                <template #append>
                  <el-button :loading="loading.customerChat" @click="sendCustomer">
                    <el-icon><Promotion /></el-icon>
                  </el-button>
                </template>
              </el-input>
            </div>
            <div class="panel">
              <div class="panel-title"><el-icon><Files /></el-icon>知识库范围</div>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="公司信息">企业背景、主营业务、联系方式</el-descriptions-item>
                <el-descriptions-item label="项目资料">中德精英人才、新加坡本硕计划</el-descriptions-item>
                <el-descriptions-item label="政策指南">德国、新加坡留学政策</el-descriptions-item>
                <el-descriptions-item label="FAQ">37 条常见问答</el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </template>

        <template v-if="activePage === 'leadEval'">
          <div class="grid two">
            <div class="panel">
              <div class="panel-title"><el-icon><Aim /></el-icon>客户画像研判</div>
              <el-input
                v-model="leadText"
                type="textarea"
                :rows="10"
                placeholder="输入客户信息，例如：张三，19岁，高中毕业，家庭条件较好，想去新加坡读本科..."
              />
              <div class="split-actions">
                <div class="quick-row">
                  <el-button @click="fillLeadSample">填入样例</el-button>
                  <el-button type="primary" :loading="loading.evaluate" @click="evaluateLead(false)">
                    <el-icon><DataAnalysis /></el-icon>
                    立即研判
                  </el-button>
                  <el-button type="success" :loading="loading.evaluate" @click="evaluateLead(true)">
                    <el-icon><FolderAdd /></el-icon>
                    研判并入库
                  </el-button>
                </div>
              </div>

              <el-divider />
              <el-upload :auto-upload="false" :show-file-list="true" :on-change="onFileChange" accept=".pdf,.docx,.xlsx,.txt">
                <el-button>
                  <el-icon><Upload /></el-icon>
                  选择客户资料 / 简历
                </el-button>
              </el-upload>
              <el-button style="margin-top: 10px" :disabled="!leadFile" :loading="loading.upload" @click="uploadLeadFile">
                上传并研判
              </el-button>
            </div>

            <div class="panel">
              <div class="panel-title"><el-icon><Medal /></el-icon>研判结果</div>
              <div v-if="!leadResult" class="muted">还没有研判结果。</div>
              <div v-else class="result-card">
                <el-tag size="large" type="success">{{ leadResult.matched_project }}</el-tag>
                <h3>客户等级：{{ leadResult.lead_level }}</h3>
                <div class="score-row">
                  <span>新加坡</span>
                  <el-progress :percentage="leadResult.singapore_score" color="#0f766e" />
                  <strong>{{ leadResult.singapore_score }}</strong>
                </div>
                <div class="score-row">
                  <span>德国</span>
                  <el-progress :percentage="leadResult.germany_score" color="#a16207" />
                  <strong>{{ leadResult.germany_score }}</strong>
                </div>
                <el-divider />
                <strong>匹配原因</strong>
                <ul>
                  <li v-for="item in leadResult.reasons" :key="item">{{ item }}</li>
                </ul>
                <strong>缺失信息</strong>
                <el-tag v-for="item in leadResult.missing_fields" :key="item" style="margin: 6px 6px 0 0" type="warning">
                  {{ item }}
                </el-tag>
                <el-divider />
                <strong>销售建议</strong>
                <p>{{ leadResult.sales_advice }}</p>
              </div>
            </div>
          </div>
        </template>

        <template v-if="activePage === 'crm'">
          <div class="panel">
            <div class="panel-title"><el-icon><UserFilled /></el-icon>客户管理 CRM</div>
            <el-table :data="leads" height="520" stripe>
              <el-table-column prop="customer_name" label="姓名" width="120" />
              <el-table-column prop="age" label="年龄" width="80" />
              <el-table-column prop="education" label="学历" width="100" />
              <el-table-column prop="intended_project" label="意向项目" min-width="220" />
              <el-table-column prop="status" label="状态" width="110">
                <template #default="{ row }">
                  <el-tag>{{ row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="contact_info" label="联系方式" width="140" />
              <el-table-column label="操作" width="220">
                <template #default="{ row }">
                  <div class="table-actions">
                    <el-button size="small" @click="selectedLead = row">详情</el-button>
                    <el-button size="small" type="success" @click="updateLead(row, '已签约')">签约</el-button>
                    <el-button size="small" type="warning" @click="updateLead(row, '跟进中')">跟进</el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <el-drawer v-model="leadDrawer" title="客户详情" size="42%">
            <template v-if="selectedLead">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="姓名">{{ selectedLead.customer_name }}</el-descriptions-item>
                <el-descriptions-item label="意向项目">{{ selectedLead.intended_project }}</el-descriptions-item>
                <el-descriptions-item label="背景">{{ selectedLead.background_info }}</el-descriptions-item>
                <el-descriptions-item label="跟进记录">{{ selectedLead.follow_up_history }}</el-descriptions-item>
              </el-descriptions>
            </template>
          </el-drawer>
        </template>

        <template v-if="activePage === 'employee'">
          <div class="grid two">
            <div class="panel chat-box">
              <div class="panel-title"><el-icon><Service /></el-icon>企业智能助手</div>
              <div class="messages">
                <div v-for="(msg, index) in employeeMessages" :key="index" class="message" :class="msg.role">
                  <div class="bubble">{{ msg.content }}</div>
                </div>
              </div>
              <div class="quick-row">
                <el-button size="small" @click="askEmployee('有哪些投诉还没有处理？')">查投诉</el-button>
                <el-button size="small" @click="askEmployee('公司打印机在哪里？')">新人指南</el-button>
                <el-button size="small" @click="askEmployee('帮我生成今天日报')">日报助手</el-button>
              </div>
              <el-input v-model="employeeInput" placeholder="输入员工指令" @keyup.enter="sendEmployee">
                <template #append>
                  <el-button :loading="loading.employeeChat" @click="sendEmployee">
                    <el-icon><Promotion /></el-icon>
                  </el-button>
                </template>
              </el-input>
            </div>
            <div class="panel">
              <div class="panel-title"><el-icon><Memo /></el-icon>员工日报</div>
              <el-input v-model="dailyContent" type="textarea" :rows="7" placeholder="输入今日工作内容" />
              <el-button style="margin-top: 10px" type="primary" @click="createDailyReport">提交日报</el-button>
              <el-divider />
              <el-timeline>
                <el-timeline-item v-for="item in dailyReports" :key="item.id" :timestamp="item.report_date">
                  {{ item.ai_summary || item.content }}
                </el-timeline-item>
              </el-timeline>
            </div>
          </div>
        </template>

        <template v-if="activePage === 'student'">
          <div class="grid two">
            <div class="panel">
              <div class="panel-title"><el-icon><Calendar /></el-icon>学生请假</div>
              <el-input v-model="leaveReason" type="textarea" :rows="4" placeholder="请输入请假原因" />
              <el-button style="margin-top: 10px" type="primary" @click="createLeave">提交请假</el-button>
              <el-divider />
              <el-table :data="leaves" height="260">
                <el-table-column prop="reason" label="原因" />
                <el-table-column prop="status" label="状态" width="100" />
                <el-table-column v-if="isEmployee" label="操作" width="160">
                  <template #default="{ row }">
                    <el-button size="small" type="success" @click="approveLeave(row, '已通过')">通过</el-button>
                    <el-button size="small" type="danger" @click="approveLeave(row, '已驳回')">驳回</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="panel">
              <div class="panel-title"><el-icon><Warning /></el-icon>投诉反馈与心理预警</div>
              <el-input v-model="feedbackContent" placeholder="投诉摘要" />
              <el-input style="margin-top: 8px" v-model="feedbackDetail" type="textarea" :rows="3" placeholder="详细说明" />
              <el-button style="margin-top: 10px" type="primary" @click="createFeedback">提交反馈</el-button>
              <el-divider />
              <el-tabs>
                <el-tab-pane label="投诉工单">
                  <el-table :data="feedbacks" height="220">
                    <el-table-column prop="content" label="内容" />
                    <el-table-column prop="status" label="状态" width="100" />
                    <el-table-column v-if="isEmployee" label="操作" width="120">
                      <template #default="{ row }">
                        <el-button size="small" type="success" @click="resolveFeedback(row)">解决</el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </el-tab-pane>
                <el-tab-pane label="心理预警">
                  <el-table :data="psychAlerts" height="220">
                    <el-table-column prop="trigger_reason" label="触发原因" />
                    <el-table-column prop="risk_level" label="等级" width="90" />
                    <el-table-column prop="status" label="状态" width="100" />
                  </el-table>
                </el-tab-pane>
              </el-tabs>
            </div>
          </div>
        </template>

        <template v-if="activePage === 'reports'">
          <div class="grid two">
            <div class="panel">
              <div class="panel-title"><el-icon><Document /></el-icon>智能报告生成</div>
              <el-radio-group v-model="reportType">
                <el-radio-button label="customer-analysis">客户经营</el-radio-button>
                <el-radio-button label="daily-summary">日报汇总</el-radio-button>
                <el-radio-button label="complaint-weekly">投诉周报</el-radio-button>
                <el-radio-button label="psych-weekly">心理周报</el-radio-button>
              </el-radio-group>
              <div style="margin-top: 14px">
                <el-button type="primary" :loading="loading.report" @click="createReport">
                  <el-icon><MagicStick /></el-icon>
                  生成报告
                </el-button>
              </div>
              <el-divider />
              <el-table :data="reports" height="360">
                <el-table-column prop="title" label="报告标题" />
                <el-table-column prop="report_type" label="类型" width="150" />
                <el-table-column prop="create_time" label="生成时间" width="180" />
                <el-table-column label="操作" width="100">
                  <template #default="{ row }">
                    <el-button size="small" @click="selectedReport = row">查看</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <div class="panel">
              <div class="panel-title"><el-icon><Reading /></el-icon>报告预览</div>
              <pre style="white-space: pre-wrap; line-height: 1.7">{{ selectedReport?.content || '请选择或生成一份报告。' }}</pre>
            </div>
          </div>
        </template>

        <template v-if="activePage === 'settings'">
          <div class="panel">
            <div class="panel-title"><el-icon><Setting /></el-icon>系统设置</div>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="后端地址">http://localhost:8000</el-descriptions-item>
              <el-descriptions-item label="前端地址">http://localhost:5173</el-descriptions-item>
              <el-descriptions-item label="Dify 地址">http://192.168.110.27</el-descriptions-item>
              <el-descriptions-item label="数据库">MySQL / edu_dify_platform</el-descriptions-item>
              <el-descriptions-item label="说明">真实密钥保存在后端 .env，前端不会暴露 Dify Key。</el-descriptions-item>
            </el-descriptions>
          </div>
        </template>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { api, currentUser, login, logout } from './api/client'

const user = ref(currentUser())
const activePage = ref('dashboard')
const health = ref({})
const dashboard = ref({})
const leads = ref([])
const selectedLead = ref(null)
const leadDrawer = computed({
  get: () => !!selectedLead.value,
  set: (value) => {
    if (!value) selectedLead.value = null
  },
})

const loginForm = reactive({ username: 'admin', password: '123456' })
const loading = reactive({
  login: false,
  customerChat: false,
  employeeChat: false,
  evaluate: false,
  upload: false,
  report: false,
})

const customerInput = ref('')
const customerMessages = ref([
  { role: 'bot', content: '你好，我是粤教服务智能咨询助手。可以咨询新加坡升学、德国双元制、报名流程和留学政策。' },
])
const employeeInput = ref('')
const employeeMessages = ref([
  { role: 'bot', content: '你好，我是企业智能助手。可以查询客户、日报、投诉、请假和新人指南。' },
])
const leadText = ref('')
const leadResult = ref(null)
const leadFile = ref(null)
const dailyContent = ref('今日跟进新加坡项目客户 3 人，德国项目客户 1 人，处理学生投诉 1 条。')
const dailyReports = ref([])
const leaveReason = ref('')
const leaves = ref([])
const feedbackContent = ref('')
const feedbackDetail = ref('')
const feedbacks = ref([])
const psychAlerts = ref([])
const reports = ref([])
const reportType = ref('customer-analysis')
const selectedReport = ref(null)

const navItems = [
  { key: 'dashboard', label: '首页仪表盘', icon: 'DataBoard', desc: '经营概览、项目分布和演示主线' },
  { key: 'customerChat', label: '客服咨询', icon: 'ChatDotRound', desc: '面向客户的 Dify 知识库问答' },
  { key: 'leadEval', label: '客户研判', icon: 'Aim', desc: '文本、PDF、Word、Excel 画像匹配' },
  { key: 'crm', label: '客户管理 CRM', icon: 'UserFilled', desc: '线索沉淀、客户详情和状态流转' },
  { key: 'employee', label: '企业助手', icon: 'Service', desc: '员工问答、日报和新人指南' },
  { key: 'student', label: '学生服务', icon: 'Calendar', desc: '请假、投诉、心理预警和服务闭环' },
  { key: 'reports', label: '智能报告', icon: 'Document', desc: '客户经营、日报、投诉和心理周报' },
  { key: 'settings', label: '系统设置', icon: 'Setting', desc: '运行地址、Dify 与数据库配置' },
]

const isEmployee = computed(() => user.value?.user_type === 'EMPLOYEE')
const roleLabel = computed(() => {
  if (!user.value) return ''
  if (user.value.employee_role === 'ADMIN') return '管理员'
  if (user.value.user_type === 'EMPLOYEE') return '员工'
  if (user.value.user_type === 'STUDENT') return '学生'
  return '客户'
})
const visibleNav = computed(() => navItems)
const currentNav = computed(() => navItems.find((item) => item.key === activePage.value))

watch(selectedLead, (value) => {
  if (value) {
    // drawer opens through computed setter
  }
})

onMounted(async () => {
  if (user.value) {
    await refreshAll()
  }
})

async function handleLogin() {
  loading.login = true
  try {
    const data = await login(loginForm.username, loginForm.password)
    user.value = data.user
    ElMessage.success('登录成功')
    await refreshAll()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.login = false
  }
}

async function quickLogin(username) {
  loginForm.username = username
  loginForm.password = '123456'
  await handleLogin()
}

function handleLogout() {
  logout()
  user.value = null
}

async function refreshAll() {
  await Promise.allSettled([
    loadHealth(),
    loadDashboard(),
    loadLeads(),
    loadDailyReports(),
    loadLeaves(),
    loadFeedbacks(),
    loadPsychAlerts(),
    loadReports(),
  ])
}

async function loadHealth() {
  const { data } = await api.get('/health')
  health.value = data
}

async function loadDashboard() {
  const { data } = await api.get('/dashboard')
  dashboard.value = data
}

async function askCustomer(text) {
  customerInput.value = text
  await sendCustomer()
}

async function sendCustomer() {
  const text = customerInput.value.trim()
  if (!text) return
  customerMessages.value.push({ role: 'user', content: text })
  customerInput.value = ''
  loading.customerChat = true
  try {
    const { data } = await api.post('/chat/customer', { message: text })
    customerMessages.value.push({ role: 'bot', content: data.answer })
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '客服助手调用失败')
  } finally {
    loading.customerChat = false
  }
}

async function askEmployee(text) {
  employeeInput.value = text
  await sendEmployee()
}

async function sendEmployee() {
  const text = employeeInput.value.trim()
  if (!text) return
  employeeMessages.value.push({ role: 'user', content: text })
  employeeInput.value = ''
  loading.employeeChat = true
  try {
    const { data } = await api.post('/chat/employee', { message: text })
    employeeMessages.value.push({ role: 'bot', content: data.answer })
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '企业助手调用失败')
  } finally {
    loading.employeeChat = false
  }
}

function fillLeadSample() {
  leadText.value = '张三，男，19岁，高中毕业，家庭经济条件较好，想出国读本科，英语一般，家长希望费用不要太高，优先考虑新加坡方向。'
}

async function evaluateLead(saveToCrm) {
  if (!leadText.value.trim()) {
    ElMessage.warning('请先输入客户信息')
    return
  }
  loading.evaluate = true
  try {
    const { data } = await api.post('/leads/evaluate', {
      text: leadText.value,
      save_to_crm: saveToCrm,
      source_type: 'text',
    })
    leadResult.value = data.evaluation
    ElMessage.success(saveToCrm ? '研判完成并已入库' : '研判完成')
    await loadLeads()
    await loadDashboard()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '研判失败')
  } finally {
    loading.evaluate = false
  }
}

function onFileChange(file) {
  leadFile.value = file.raw
}

async function uploadLeadFile() {
  if (!leadFile.value) return
  loading.upload = true
  try {
    const form = new FormData()
    form.append('file', leadFile.value)
    const { data } = await api.post('/leads/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    leadResult.value = data.evaluation
    ElMessage.success('文件研判完成')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '文件上传失败')
  } finally {
    loading.upload = false
  }
}

async function loadLeads() {
  const { data } = await api.get('/leads')
  leads.value = data
}

async function updateLead(row, status) {
  await api.put(`/leads/${row.id}/status`, { status, follow_up_note: `状态更新为${status}` })
  ElMessage.success('客户状态已更新')
  await loadLeads()
  await loadDashboard()
}

async function createDailyReport() {
  if (!dailyContent.value.trim()) return
  await api.post('/daily-reports', { content: dailyContent.value })
  ElMessage.success('日报已提交')
  await loadDailyReports()
}

async function loadDailyReports() {
  const { data } = await api.get('/daily-reports')
  dailyReports.value = data
}

async function createLeave() {
  if (!leaveReason.value.trim()) return
  await api.post('/student/leave', { reason: leaveReason.value })
  leaveReason.value = ''
  ElMessage.success('请假已提交')
  await loadLeaves()
  await loadDashboard()
}

async function loadLeaves() {
  const { data } = await api.get('/student/leave')
  leaves.value = data
}

async function approveLeave(row, status) {
  await api.put(`/student/leave/${row.id}/approve`, { status })
  ElMessage.success('审批已更新')
  await loadLeaves()
  await loadDashboard()
}

async function createFeedback() {
  if (!feedbackContent.value.trim()) return
  await api.post('/student/feedback', {
    content: feedbackContent.value,
    detail: feedbackDetail.value,
  })
  feedbackContent.value = ''
  feedbackDetail.value = ''
  ElMessage.success('反馈已提交')
  await loadFeedbacks()
  await loadDashboard()
}

async function loadFeedbacks() {
  const { data } = await api.get('/student/feedback')
  feedbacks.value = data
}

async function resolveFeedback(row) {
  await api.put(`/student/feedback/${row.id}`, { status: '已解决', solution: '已联系顾问跟进并同步处理结果。' })
  ElMessage.success('工单已解决')
  await loadFeedbacks()
  await loadDashboard()
}

async function loadPsychAlerts() {
  if (!user.value || user.value.user_type !== 'EMPLOYEE') {
    psychAlerts.value = []
    return
  }
  const { data } = await api.get('/student/psych-alerts')
  psychAlerts.value = data
}

async function createReport() {
  loading.report = true
  try {
    const { data } = await api.post('/reports', { report_type: reportType.value })
    selectedReport.value = data.report
    ElMessage.success('报告已生成')
    await loadReports()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '报告生成失败')
  } finally {
    loading.report = false
  }
}

async function loadReports() {
  if (!user.value || user.value.user_type !== 'EMPLOYEE') {
    reports.value = []
    return
  }
  const { data } = await api.get('/reports')
  reports.value = data
  selectedReport.value ||= data[0]
}
</script>
