# REALPLAN: OmniVibe Pro 구현 계획

## 📋 프로젝트 개요

**목표**: Rails 8 + SQLite3 + Hotwire 기반 관리자 대시보드를 FastAPI AI 백엔드와 통합하여, 실시간 AI 영상 자동화 SaaS 플랫폼 구축

**현재 상태**:
- ✅ FastAPI 백엔드 구축 완료 (AI 파이프라인, 에이전트)
- ✅ Next.js 프론트엔드 Studio UI 완료 (사용자 워크플로우)
- ⚠️ transformers 라이브러리 UTF-8 문제로 일부 에이전트 비활성화
- 🆕 Rails 8 Admin Dashboard 신규 구축 필요

**기술 스택**:
- **AI Backend**: FastAPI + LangGraph + Celery
- **Admin Backend**: Rails 8 + Hotwire + SQLite3/PostgreSQL
- **User Frontend**: Next.js 14 + TypeScript + SQLite3
- **Real-time**: Hotwire Turbo Streams (Admin), WebSocket (Studio)

---

## Phase 0: 환경 설정 및 Rails 프로젝트 초기화

### 0.1 Rails 8 프로젝트 생성
**목표**: Rails 8 + Hotwire + SQLite3 기반 Admin 앱 초기화

**작업**:
```bash
cd /Volumes/Extreme\ SSD/02_GitHub.nosync/30_OmniVibePro
rails new admin --skip-javascript --css=tailwind --database=sqlite3
cd admin
bundle add hotwire-rails
rails hotwire:install
```

**설정**:
- `config/database.yml`: SQLite3 개발/테스트, PostgreSQL 프로덕션
- `Gemfile`: `solid_queue`, `solid_cache`, `solid_cable` 추가 (Rails 8 defaults)
- `.env`: FastAPI 백엔드 URL 설정 (`FASTAPI_BASE_URL=http://localhost:8000`)

**검증**:
```bash
rails server -p 3000
curl http://localhost:3000
```

### 0.2 모델 및 데이터베이스 설계
**목표**: Admin 전용 데이터베이스 스키마 설계

**모델**:
```ruby
# app/models/admin_user.rb - 관리자 계정
class AdminUser < ApplicationRecord
  has_secure_password
  has_many :audit_logs
end

# app/models/client.rb - 클라이언트 (이미 FastAPI에 존재)
class Client < ApplicationRecord
  has_many :campaigns
  has_many :contents, through: campaigns
end

# app/models/campaign.rb - 캠페인
class Campaign < ApplicationRecord
  belongs_to :client
  has_many :contents
  has_many :resources
end

# app/models/content.rb - 콘텐츠 (영상)
class Content < ApplicationRecord
  belongs_to :campaign
  enum status: [:draft, :script_generated, :audio_generated, :video_rendered, :published]
end

# app/models/audit_log.rb - 감사 로그
class AuditLog < ApplicationRecord
  belongs_to :admin_user
end
```

**마이그레이션**:
```bash
rails g model AdminUser email:string password_digest:string name:string role:string
rails g model Client name:string industry:string contact_email:string
rails g model Campaign name:string client:references status:string concept_gender:string
rails g model Content title:string campaign:references status:integer script:text audio_url:string video_url:string
rails g model AuditLog admin_user:references action:string resource_type:string resource_id:integer details:json
rails db:migrate
```

---

## Phase 1: Admin 인증 및 대시보드 기본 구조

### 1.1 인증 시스템 (Devise 대신 Rails 내장 기능 사용)
**목표**: 간단한 세션 기반 인증

**컨트롤러**:
```ruby
# app/controllers/sessions_controller.rb
class SessionsController < ApplicationController
  def new; end

  def create
    user = AdminUser.find_by(email: params[:email])
    if user&.authenticate(params[:password])
      session[:admin_user_id] = user.id
      redirect_to dashboard_path
    else
      flash.now[:alert] = "Invalid credentials"
      render :new, status: :unprocessable_entity
    end
  end

  def destroy
    session[:admin_user_id] = nil
    redirect_to login_path
  end
end
```

**뷰** (Hotwire + Tailwind):
```erb
<!-- app/views/sessions/new.html.erb -->
<div class="min-h-screen flex items-center justify-center bg-gray-900">
  <div class="max-w-md w-full bg-gray-800 rounded-lg p-8">
    <h1 class="text-2xl font-bold text-white mb-6">OmniVibe Admin</h1>
    <%= form_with url: session_path, data: { turbo: false } do |f| %>
      <%= f.email_field :email, placeholder: "Email", class: "w-full px-4 py-2 mb-4 bg-gray-700 text-white rounded" %>
      <%= f.password_field :password, placeholder: "Password", class: "w-full px-4 py-2 mb-4 bg-gray-700 text-white rounded" %>
      <%= f.submit "Login", class: "w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded" %>
    <% end %>
  </div>
</div>
```

### 1.2 대시보드 레이아웃
**목표**: Turbo Frame 기반 실시간 대시보드

**레이아웃**:
```erb
<!-- app/views/layouts/admin.html.erb -->
<!DOCTYPE html>
<html>
<head>
  <title>OmniVibe Admin</title>
  <%= csrf_meta_tags %>
  <%= csp_meta_tag %>
  <%= stylesheet_link_tag "tailwind", "inter-font", "data-turbo-track": "reload" %>
  <%= javascript_importmap_tags %>
</head>
<body class="bg-gray-900 text-white">
  <%= render "shared/navbar" %>
  <div class="flex">
    <%= render "shared/sidebar" %>
    <main class="flex-1 p-6">
      <%= turbo_frame_tag "main_content" do %>
        <%= yield %>
      <% end %>
    </main>
  </div>
</body>
</html>
```

**사이드바** (Stimulus 컨트롤러):
```erb
<!-- app/views/shared/_sidebar.html.erb -->
<nav class="w-64 bg-gray-800 h-screen p-4">
  <%= link_to "Dashboard", dashboard_path, class: "block py-2 px-4 hover:bg-gray-700 rounded", data: { turbo_frame: "main_content" } %>
  <%= link_to "Clients", clients_path, class: "block py-2 px-4 hover:bg-gray-700 rounded", data: { turbo_frame: "main_content" } %>
  <%= link_to "Campaigns", campaigns_path, class: "block py-2 px-4 hover:bg-gray-700 rounded", data: { turbo_frame: "main_content" } %>
  <%= link_to "Contents", contents_path, class: "block py-2 px-4 hover:bg-gray-700 rounded", data: { turbo_frame: "main_content" } %>
  <%= link_to "AI Agents", agents_path, class: "block py-2 px-4 hover:bg-gray-700 rounded", data: { turbo_frame: "main_content" } %>
  <%= link_to "Logs", audit_logs_path, class: "block py-2 px-4 hover:bg-gray-700 rounded", data: { turbo_frame: "main_content" } %>
</nav>
```

---

## Phase 2: FastAPI 연동 및 AI 작업 트리거

### 2.1 FastAPI HTTP 클라이언트 서비스
**목표**: Rails에서 FastAPI 백엔드 호출

**서비스 클래스**:
```ruby
# app/services/fastapi_client.rb
class FastapiClient
  BASE_URL = ENV.fetch("FASTAPI_BASE_URL", "http://localhost:8000")

  def self.generate_script(params)
    response = HTTParty.post(
      "#{BASE_URL}/api/v1/writer/generate",
      body: params.to_json,
      headers: { "Content-Type" => "application/json" }
    )
    JSON.parse(response.body)
  end

  def self.generate_audio(params)
    response = HTTParty.post(
      "#{BASE_URL}/api/v1/audio/generate",
      body: params.to_json,
      headers: { "Content-Type" => "application/json" }
    )
    JSON.parse(response.body)
  end

  def self.check_audio_status(task_id)
    response = HTTParty.get("#{BASE_URL}/api/v1/audio/status/#{task_id}")
    JSON.parse(response.body)
  end

  def self.render_video(params)
    response = HTTParty.post(
      "#{BASE_URL}/api/v1/video/render",
      body: params.to_json,
      headers: { "Content-Type" => "application/json" }
    )
    JSON.parse(response.body)
  end
end
```

**Gemfile 추가**:
```ruby
gem 'httparty'
```

### 2.2 컨텐츠 생성 워크플로우 컨트롤러
**목표**: Admin에서 AI 파이프라인 트리거

**컨트롤러**:
```ruby
# app/controllers/contents_controller.rb
class ContentsController < ApplicationController
  def index
    @contents = Content.includes(:campaign).order(created_at: :desc)
  end

  def new
    @content = Content.new
    @campaigns = Campaign.all
  end

  def create
    @content = Content.create(content_params.merge(status: :draft))

    # 비동기로 스크립트 생성
    GenerateScriptJob.perform_later(@content.id)

    respond_to do |format|
      format.html { redirect_to content_path(@content) }
      format.turbo_stream
    end
  end

  def show
    @content = Content.find(params[:id])
  end

  def regenerate_script
    @content = Content.find(params[:id])
    GenerateScriptJob.perform_later(@content.id, regenerate: true)
    redirect_to content_path(@content), notice: "스크립트 재생성 시작"
  end

  def generate_audio
    @content = Content.find(params[:id])
    GenerateAudioJob.perform_later(@content.id)
    redirect_to content_path(@content), notice: "오디오 생성 시작"
  end

  private

  def content_params
    params.require(:content).permit(:title, :campaign_id, :topic, :platform, :target_duration)
  end
end
```

### 2.3 Solid Queue 백그라운드 작업
**목표**: Rails 8의 Solid Queue로 AI 작업 관리

**Job 클래스**:
```ruby
# app/jobs/generate_script_job.rb
class GenerateScriptJob < ApplicationJob
  queue_as :default

  def perform(content_id, regenerate: false)
    content = Content.find(content_id)

    result = FastapiClient.generate_script(
      content_id: content.id,
      campaign_name: content.campaign.name,
      topic: content.title,
      platform: content.platform,
      target_duration: content.target_duration || 180,
      regenerate: regenerate
    )

    if result["success"]
      content.update!(
        script: result["script"],
        status: :script_generated
      )

      # Turbo Stream으로 실시간 UI 업데이트
      broadcast_update(content)
    else
      content.update!(status: :draft)
      Rails.logger.error("Script generation failed: #{result['error']}")
    end
  end

  private

  def broadcast_update(content)
    Turbo::StreamsChannel.broadcast_replace_to(
      "content_#{content.id}",
      target: "content_status",
      partial: "contents/status",
      locals: { content: content }
    )
  end
end

# app/jobs/generate_audio_job.rb
class GenerateAudioJob < ApplicationJob
  queue_as :default

  def perform(content_id)
    content = Content.find(content_id)

    result = FastapiClient.generate_audio(
      text: content.script,
      voice_id: "rachel",
      language: "ko",
      accuracy_threshold: 0.95,
      max_attempts: 3
    )

    if result["task_id"]
      # 폴링으로 상태 확인
      PollAudioStatusJob.set(wait: 5.seconds).perform_later(content.id, result["task_id"])
    end
  end
end

# app/jobs/poll_audio_status_job.rb
class PollAudioStatusJob < ApplicationJob
  queue_as :default

  def perform(content_id, task_id, attempt = 0)
    content = Content.find(content_id)
    status = FastapiClient.check_audio_status(task_id)

    case status["status"]
    when "SUCCESS"
      content.update!(
        audio_url: status.dig("info", "result", "audio_path"),
        status: :audio_generated
      )
      broadcast_update(content)
    when "FAILURE"
      Rails.logger.error("Audio generation failed: #{status['info']}")
    else
      # 최대 30초 대기 (6회 폴링)
      if attempt < 6
        PollAudioStatusJob.set(wait: 5.seconds).perform_later(content_id, task_id, attempt + 1)
      end
    end
  end

  private

  def broadcast_update(content)
    Turbo::StreamsChannel.broadcast_replace_to(
      "content_#{content.id}",
      target: "content_status",
      partial: "contents/status",
      locals: { content: content }
    )
  end
end
```

---

## Phase 3: Turbo Streams 실시간 UI

### 3.1 실시간 상태 업데이트
**목표**: 백그라운드 작업 진행 상황을 페이지 새로고침 없이 표시

**뷰**:
```erb
<!-- app/views/contents/show.html.erb -->
<%= turbo_stream_from "content_#{@content.id}" %>

<div class="max-w-4xl mx-auto">
  <h1 class="text-3xl font-bold mb-6"><%= @content.title %></h1>

  <%= turbo_frame_tag "content_status" do %>
    <%= render "status", content: @content %>
  <% end %>

  <div class="mt-8">
    <h2 class="text-xl font-semibold mb-4">스크립트</h2>
    <div class="bg-gray-800 p-6 rounded-lg">
      <%= simple_format(@content.script || "스크립트 생성 중...") %>
    </div>

    <% if @content.script_generated? %>
      <div class="mt-4 space-x-4">
        <%= button_to "스크립트 재생성", regenerate_script_content_path(@content),
            method: :post, class: "bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded" %>
        <%= button_to "오디오 생성", generate_audio_content_path(@content),
            method: :post, class: "bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded" %>
      </div>
    <% end %>
  </div>

  <% if @content.audio_generated? %>
    <div class="mt-8">
      <h2 class="text-xl font-semibold mb-4">오디오</h2>
      <audio controls class="w-full">
        <source src="<%= @content.audio_url %>" type="audio/mpeg">
      </audio>
    </div>
  <% end %>
</div>
```

**파셜**:
```erb
<!-- app/views/contents/_status.html.erb -->
<div class="bg-gray-800 p-4 rounded-lg mb-6">
  <div class="flex items-center justify-between">
    <span class="text-lg">상태:</span>
    <span class="px-3 py-1 rounded <%= status_color(@content.status) %>">
      <%= @content.status.humanize %>
    </span>
  </div>

  <% if @content.draft? || @content.script_generated? %>
    <div class="mt-4">
      <div class="animate-pulse text-yellow-400">⏳ 처리 중...</div>
    </div>
  <% end %>
</div>
```

### 3.2 Stimulus 컨트롤러 (클라이언트 사이드 인터랙션)
**목표**: 실시간 카운터, 자동 리프레시 등

**컨트롤러**:
```javascript
// app/javascript/controllers/auto_refresh_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = { interval: Number }

  connect() {
    this.startRefreshing()
  }

  disconnect() {
    this.stopRefreshing()
  }

  startRefreshing() {
    this.refreshTimer = setInterval(() => {
      this.element.reload()
    }, this.intervalValue || 5000)
  }

  stopRefreshing() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer)
    }
  }
}
```

**사용**:
```erb
<%= turbo_frame_tag "content_list",
    src: contents_path,
    data: { controller: "auto-refresh", auto_refresh_interval_value: 5000 } do %>
  <%= render @contents %>
<% end %>
```

---

## Phase 4: 대시보드 통계 및 차트

### 4.1 메인 대시보드
**목표**: 실시간 통계 및 차트 (Chart.js + Turbo Frames)

**컨트롤러**:
```ruby
# app/controllers/dashboard_controller.rb
class DashboardController < ApplicationController
  def index
    @total_clients = Client.count
    @total_campaigns = Campaign.count
    @total_contents = Content.count
    @pending_contents = Content.where(status: [:draft, :script_generated, :audio_generated]).count
    @published_contents = Content.where(status: :published).count

    @recent_contents = Content.includes(:campaign).order(created_at: :desc).limit(10)
    @recent_logs = AuditLog.includes(:admin_user).order(created_at: :desc).limit(20)
  end
end
```

**뷰**:
```erb
<!-- app/views/dashboard/index.html.erb -->
<div class="grid grid-cols-4 gap-6 mb-8">
  <%= render "stat_card", title: "Clients", value: @total_clients, icon: "👥" %>
  <%= render "stat_card", title: "Campaigns", value: @total_campaigns, icon: "📋" %>
  <%= render "stat_card", title: "Contents", value: @total_contents, icon: "🎬" %>
  <%= render "stat_card", title: "Pending", value: @pending_contents, icon: "⏳" %>
</div>

<div class="grid grid-cols-2 gap-6">
  <div class="bg-gray-800 p-6 rounded-lg">
    <h2 class="text-xl font-semibold mb-4">Recent Contents</h2>
    <%= turbo_frame_tag "recent_contents", src: recent_contents_path, refresh: "morph" do %>
      <%= render @recent_contents %>
    <% end %>
  </div>

  <div class="bg-gray-800 p-6 rounded-lg">
    <h2 class="text-xl font-semibold mb-4">Activity Log</h2>
    <%= turbo_frame_tag "recent_logs" do %>
      <%= render @recent_logs %>
    <% end %>
  </div>
</div>
```

---

## Phase 5: 감사 로그 및 보안

### 5.1 감사 로그 자동 기록
**목표**: 모든 CRUD 작업 자동 로그

**Concern**:
```ruby
# app/models/concerns/auditable.rb
module Auditable
  extend ActiveSupport::Concern

  included do
    after_create :log_create
    after_update :log_update
    after_destroy :log_destroy
  end

  private

  def log_create
    AuditLog.create!(
      admin_user: Current.admin_user,
      action: "create",
      resource_type: self.class.name,
      resource_id: self.id,
      details: attributes
    )
  end

  def log_update
    AuditLog.create!(
      admin_user: Current.admin_user,
      action: "update",
      resource_type: self.class.name,
      resource_id: self.id,
      details: saved_changes
    )
  end

  def log_destroy
    AuditLog.create!(
      admin_user: Current.admin_user,
      action: "destroy",
      resource_type: self.class.name,
      resource_id: self.id,
      details: attributes
    )
  end
end
```

**모델에 적용**:
```ruby
class Content < ApplicationRecord
  include Auditable
  # ...
end
```

### 5.2 권한 관리 (Pundit)
**목표**: Role 기반 액세스 제어

**Gemfile**:
```ruby
gem 'pundit'
```

**Policy**:
```ruby
# app/policies/content_policy.rb
class ContentPolicy < ApplicationPolicy
  def create?
    user.role.in?(['admin', 'editor'])
  end

  def update?
    user.role.in?(['admin', 'editor'])
  end

  def destroy?
    user.role == 'admin'
  end
end
```

---

## Phase 6: 프로덕션 배포 준비

### 6.1 환경 변수 및 시크릿 관리
**설정**:
```yaml
# config/credentials.yml.enc (rails credentials:edit)
fastapi:
  base_url: https://api.omnivibepro.com

database:
  production:
    url: <%= ENV['DATABASE_URL'] %>

secret_key_base: <%= ENV['SECRET_KEY_BASE'] %>
```

### 6.2 PostgreSQL 전환 (프로덕션)
**Gemfile**:
```ruby
group :production do
  gem 'pg'
end

group :development, :test do
  gem 'sqlite3'
end
```

**database.yml**:
```yaml
production:
  adapter: postgresql
  url: <%= ENV['DATABASE_URL'] %>
  pool: <%= ENV.fetch("RAILS_MAX_THREADS") { 5 } %>
```

### 6.3 Solid Queue 프로덕션 설정
**config/queue.yml**:
```yaml
production:
  dispatchers:
    - polling_interval: 1
      batch_size: 500
  workers:
    - queues: "*"
      threads: 3
      processes: 2
      polling_interval: 0.1
```

---

## 타임라인

| Phase | 예상 시간 | 목표 |
|-------|----------|------|
| Phase 0 | 2시간 | Rails 8 프로젝트 초기화 및 DB 설계 |
| Phase 1 | 4시간 | 인증 및 대시보드 기본 구조 |
| Phase 2 | 6시간 | FastAPI 연동 및 백그라운드 작업 |
| Phase 3 | 4시간 | Turbo Streams 실시간 UI |
| Phase 4 | 3시간 | 대시보드 통계 및 차트 |
| Phase 5 | 3시간 | 감사 로그 및 보안 |
| Phase 6 | 2시간 | 프로덕션 배포 준비 |
| **합계** | **24시간** | **MVP 완성** |

---

## 다음 단계

1. **Phase 0 실행**: `rails new admin` 실행 및 기본 설정
2. **FastAPI 연동 테스트**: HTTParty로 `/api/v1/audio/generate` 호출 테스트
3. **Turbo 테스트**: 간단한 Turbo Frame/Stream 예제 구현
4. **점진적 마이그레이션**: Next.js Studio와 병행 운영하며 Admin 기능 추가

---

## 주요 결정 사항

✅ **Rails 8의 Modern Defaults 사용**:
- Solid Queue (백그라운드 작업)
- Solid Cache (캐싱)
- Solid Cable (WebSocket 대체)

✅ **Hotwire로 실시간 UI**:
- Turbo Frames: 페이지 일부만 리로드
- Turbo Streams: 서버 푸시 업데이트
- Stimulus: 최소한의 JavaScript

✅ **FastAPI와의 분리**:
- Rails: Admin 대시보드, 비즈니스 로직, 감사 로그
- FastAPI: AI 파이프라인, 에이전트, 비디오 렌더링
- HTTP API로 통신 (REST)

✅ **점진적 전환**:
- Next.js Studio는 그대로 유지 (사용자용)
- Rails Admin은 별도 앱으로 구축 (관리자용)
