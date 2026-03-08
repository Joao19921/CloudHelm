# Segurança e Governança - CloudHelm

## Visão Geral

CloudHelm implementa um sistema completo de segurança e governança para controlar acesso a plataforma, rastrear ações administrativas, gerenciar permissões baseadas em funções (role-based access control) e garantir conformidade com políticas de segurança.

---

## 1. Modelo de Controle de Acesso

### 1.1 Funções (Roles)

CloudHelm suporta três funções principais:

| Função | Permissões | Casos de Uso |
|--------|-----------|------------|
| **admin** | Controle total: aprovação de usuários, gestão de funções, acesso a logs de auditoria, configuração de IA, revogação de acesso | Administradores do sistema, gerentes de segurança |
| **reviewer** | Aprovação de novos usuários, visualização de logs de auditoria (auditoria) | Responsáveis por onboarding, compliance officers |
| **user** | Acesso à plataforma para criar demandas e consultar catálogo de nuvem | Usuários finais da plataforma |

### 1.2 Fluxo de Aprovação

1. **Registro/Login**: Novo usuário autoriza via GitHub ou email/senha
2. **Estado Pendente**: Usuário fica em estado `is_approved=False` até aprovação
3. **Aprovação**: Administrador ou reviewer aprova usuário via endpoint `/api/backoffice/users/{user_id}/approve`
4. **Timestamp**: Campo `approved_at` registra momento da aprovação
5. **Acesso Liberado**: Usuário pode agora fazer login e acessar plataforma

### 1.3 Bootstrap Admin

- **Primeiro Usuário**: O primeiro usuário registrado é automaticamente promovido a `admin`
- **GitHub Allowlist**: Usuários no allowlist (GITHUB_ADMIN_ALLOWLIST env) são criados como admins imediatamente
- **Sem Verificação Manual**: Primeiros admins não precisam de aprovação manual

**Configuração**:
```bash
export GITHUB_ADMIN_ALLOWLIST="user1,user2,user3"
```

---

## 2. Auditoria e Rastreamento

### 2.1 Log de Auditoria (AuditLog)

Toda ação administrativa é registrada na tabela `audit_log` com:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único do log |
| `user_id` | FK | ID do usuário admin que executou a ação |
| `action` | STRING | Tipo de ação (user_approved, access_revoked, role_changed, etc.) |
| `target_user_id` | FK (nullable) | ID do usuário afetado pela ação |
| `description` | TEXT | Descrição legível da ação |
| `details` | JSONB | Dados estruturados adicionais (old_role, new_role, expiration date, etc.) |
| `ip_address` | STRING | IP do cliente que fez a requisição |
| `created_at` | TIMESTAMP | Quando a ação foi registrada |

### 2.2 Ações Rastreadas

| Ação | Descrição | Gatilho |
|------|-----------|---------|
| `user_approved` | Usuário aprovado | POST /api/backoffice/users/{user_id}/approve |
| `access_revoked` | Acesso revogado | POST /api/backoffice/users/{user_id}/revoke |
| `role_changed` | Função do usuário alterada | POST /api/backoffice/users/{user_id}/role |
| `temporary_access_granted` | Acesso temporário concedido | POST /api/backoffice/users/temporary-access |
| `access_expired` | Acesso expirou (automático) | Sistema (durante login) |

### 2.3 Acessar Logs de Auditoria

**Endpoint**:
```bash
GET /api/backoffice/audit-logs?limit=100
```

**Response**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "action": "user_approved",
    "description": "User user@example.com approved by admin@example.com",
    "admin_id": 1,
    "target_user_id": 5,
    "created_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "action": "role_changed",
    "description": "Role changed from user to reviewer",
    "admin_id": 1,
    "target_user_id": 3,
    "created_at": "2024-01-15T11:45:00Z"
  }
]
```

### 2.4 Retenção de Dados

- **Logs de Auditoria**: Mantidos indefinidamente para conformidade
- **Política de Exclusão**: Apenas administradores podem deletar logs (operação manual para casos específicos)
- **GDPR/Privacidade**: Usuários deletados têm seus logs anônimos opcionalmente

---

## 3. Notificações por Email

### 3.1 Eventos de Email

| Evento | Quando Enviado | Destinatário | Conteúdo |
|--------|----------------|-------------|----------|
| **Aprovação** | Usuário aprovado | Email do usuário | "Sua conta foi aprovada. Você pode fazer login em CloudHelm." |
| **Revogação** | Acesso revogado | Email do usuário | "Seu acesso foi revogado. Contate um administrador se isso for um erro." |
| **Mudança de Função** | Função alterada | Email do usuário | "Sua função foi alterada para [nova_função]." |
| **Expiração em 7 dias** | Login (semana antes de expirar) | Email do usuário | "Seu acesso temporário expira em X dias. Contate um admin para renovar." |

### 3.2 Configuração de Email

**Variáveis de Ambiente**:
```bash
# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@cloudhelm.example.com
SMTP_FROM_NAME=CloudHelm Admin
```

**Ativar/Desativar**:
```python
# emails estão desativados por padrão
# se SMTP_SERVER não estiver configurado, todas as chamadas de email são silenciosamente ignoradas
```

---

## 4. Expiração de Acesso

### 4.1 Acesso Temporário

Administradores podem conceder acesso temporário para:
- Testes de plataforma
- Onboarding de período limitado
- Contractor/parceiro por tempo determinado

### 4.2 Configurar Expiração

**Endpoint**:
```bash
POST /api/backoffice/users/temporary-access
Content-Type: application/json

{
  "user_ids": [5, 7, 10],
  "days": 14
}
```

**Response**:
```json
{
  "message": "Temporary access granted to 3 user(s)",
  "expires_at": "2024-01-29T10:30:00Z",
  "updated_count": 3
}
```

### 4.3 Verificação de Expiração

- **Verificado no Login**: Se `access_expires_at < now()`, login é bloqueado com 403
- **Aviso Prévio**: Email enviado 7 dias antes da expiração
- **Renovação**: Admin pode chamar endpoint novamente para estender acesso

### 4.4 Schema do Usuário

```python
class User(Base):
    id: int
    name: str
    email: str
    
    # Access Control
    is_approved: bool = False
    role: str = "user"  # admin | reviewer | user
    
    # Timestamps
    approved_at: Optional[datetime] = None
    access_expires_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_at: datetime
    
    # Relationships
    audit_logs: List[AuditLog]  # Ações que este admin realizou
```

---

## 5. API Endpoints de Governança

### 5.1 Gestão de Usuários

**Listar Usuários**:
```bash
GET /api/backoffice/users
Authorization: Bearer {admin_token}
```

Response inclui: `id`, `name`, `email`, `role`, `is_approved`, `approved_at`, `access_expires_at`, `last_login_at`

**Aprovar Usuário**:
```bash
POST /api/backoffice/users/{user_id}/approve
Authorization: Bearer {admin_token}
```

**Revogar Acesso**:
```bash
POST /api/backoffice/users/{user_id}/revoke
Authorization: Bearer {admin_token}
```

**Mudar Função**:
```bash
POST /api/backoffice/users/{user_id}/role
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "role": "reviewer"
}
```

### 5.2 Aprovação em Massa

**Aprovar Múltiplos Usuários**:
```bash
POST /api/backoffice/users/bulk-approve
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "user_ids": [2, 4, 6, 8]
}
```

Response:
```json
{
  "message": "Approved 4/4 users",
  "approved_count": 4
}
```

### 5.3 Logs de Auditoria

**Obter Últimos Logs**:
```bash
GET /api/backoffice/audit-logs?limit=50
Authorization: Bearer {admin_token}
```

---

## 6. Cenários de Segurança e Conformidade

### 6.1 Proteção contra Acesso Não Autorizado

| Cenário | Controle | Implementação |
|---------|----------|---|
| Usuário não aprovado tenta fazer login | Bloqueio (403) | `if not user.is_approved: raise 403` |
| Acesso temporário expirado | Bloqueio (403) | `if access_expires_at < now(): raise 403` |
| Usuário não-admin tenta acessar backoffice | Bloqueio (403) | Dependency `get_admin_user()` em endpoints |
| Modificação de campo sensível sem log | Auditoria | Toda ação admin registra em `audit_log` |

### 6.2 Segregação de Funções

```
Admin     →  Pode: aprovação, gestão de roles, revogação, config IA
Reviewer  →  Pode: aprovação, visualizar logs
User      →  Pode: criar demandas, ler catálogo
```

### 6.3 Conformidade

#### GDPR
- ✅ **Direito ao Esquecimento**: Usuários podem solicitar exclusão (endpoint `/api/auth/delete-account`)
- ✅ **Auditoria**: Logs permitem rastrear quem acessou quê
- ✅ **Consentimento**: Email de aprovação confirma acesso

#### ISO 27001
- ✅ **Controle de Acesso**: Role-based, aprovação manual, expiração
- ✅ **Auditoria**: Todos eventos admin registrados com IP e timestamp
- ✅ **Segregação**: Admin ≠ User, separação de privilégios

---

## 7. Melhores Práticas de Segurança

### 7.1 Para Administradores

1. **Aprovar com Cuidado**: Revise email/GitHub do usuário antes de aprovar
2. **Auditar Regularmente**: Verifique logs mensalmente para atividades suspeitas
3. **Revogar Acesso**: Remove usuários inativos após 90 dias
4. **Renovar Temporários**: Revise expiração de acessos temporários regularmente
5. **Segregação**: Não use admin para operações user (use sua função correcta)

### 7.2 Para Usuários

1. **Senha Forte**: Use senhas com 12+ caracteres, misture tipos
2. **GitHub OAuth**: Prefira OAuth quando possível (mais seguro)
3. **Avisos de Expiração**: Responda a emails sobre acesso expirando
4. **Não Compartilhe Token**: Access tokens são pessoais, não compartilhe

### 7.3 Para Deployment

1. **HTTPS Sempre**: Never expose backend sem SSL/TLS
2. **Secrets em ENV**: Nunca commite SMTP_PASSWORD, GITHUB_CLIENT_SECRET
3. **Database Encryption**: Use Supabase row-level security se possível
4. **Backup Logs**: Faça backup de audit_logs regularmente para arquivo
5. **IP Whitelist**: Considere restringir acesso à backoffice para IPs conhecidos

---

## 8. Troubleshooting

### Problema: Usuário aprovado não consegue fazer login

**Causa Possível**: Acesso expirado
**Solução**:
```bash
SELECT * FROM users WHERE id = X;
# Verifique access_expires_at

# Se expirou, renove:
POST /api/backoffice/users/temporary-access
  { "user_ids": [X], "days": 30 }
```

### Problema: Email de notificação não foi enviado

**Causa Possível**: SMTP não está configurado
**Solução**:
```bash
# Verifique environment
echo $SMTP_SERVER

# Se vazio, configure:
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password

# Reinicie backend
```

### Problema: Admin quer ver todos os logs de um usuário

**Solução**:
```python
from app.services.audit_service import AuditService
logs = AuditService.get_logs_for_user(db, user_id=5)
```

---

## 9. Roadmap de Segurança

### Curto Prazo (V1.1)
- [ ] Two-factor authentication (2FA) para admins
- [ ] IP whitelisting para backoffice
- [ ] Notificações em tempo real para admin de eventos críticos

### Médio Prazo (V1.2)
- [ ] Single Sign-On (SSO) com Azure AD / Okta
- [ ] Session timeout personalizado
- [ ] Rate limiting em endpoints de login

### Longo Prazo (V2.0)
- [ ] Hardware tokens (security keys)
- [ ] Compliance reports automatizados (ISO, GDPR)
- [ ] Machine learning para detectar comportamento anômalo

---

## 10. Contato e Suporte

Para questões de segurança:
1. **Vulnerabilidade Zero-Day**: Contate security@cloudhelm.example.com
2. **Incidente de Segurança**: Escalpe para gerente de compliance
3. **Dúvidas sobre Acesso**: Abra ticket com seu admin

---

**Última Atualização**: Janeiro 2024  
**Versão**: 1.0  
**Mantido Por**: Equipe de Segurança CloudHelm
