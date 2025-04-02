import config
from openai import OpenAI

class LLMAnalysis:
    def __init__(self, model_name):
        if model_name not in ['OpenAI', 'Deepseek']:
            raise ValueError("Model must be 'OpenAI' or 'Deepseek'")
        else:
            self.model_config = config.OpenAI if model_name == 'OpenAI' else config.DeepSeek
        self.model = model_name
        self.client = OpenAI(api_key=self.model_config.API_KEY)
        self.role = "developer"
        
    def generate_prompt(self, SI):
        """
        Generates a structured prompt for the model to analyze whether the 
        detected code smell and applied refactoring correctly correspond to the code changes.
        """
        smell_kind = SI["smell_versions"][-1]["smell_kind"]
        smell_type = SI["smell_versions"][-1]["smell_name"]
        smell_file_name = self._get_file_name(SI["smell_versions"][-1]["package_name"], SI["smell_versions"][-1]["type_name"])
        smell_method = SI["smell_versions"][-1]["method_name"]
        smell_method_range = (SI['smell_versions'][-1]['method_start_ln'], SI['smell_versions'][-1]['method_end_ln'])
        smell_cause = SI["smell_versions"][-1]["cause"]
        
        ref = SI["removed_by_refactorings"][0]
        ref_type = ref["type_name"]
        ref_description = ref["description"]
        ref_left_changes = ref["left_changes"]
        ref_right_changes = ref["right_changes"]
        
        # Generate a structured prompt
        prompt = f"""
        You are an expert software developer that understand code smells and refactoring with very good grasp and practical knowledge in Java programming.
        Instructions:
        - correct_mapping: Respond with `True` if the refactoring effectively removes the code smell; respond with `False` if it does not, and provide a brief explanation.
        - decreases_severity: Respond with `True` if the refactoring reduces the severity of the code smell without completely eliminating it; respond with `False` if it does not reduce or increases the severity.
        - Output Format: The answer must be in the format: `{{"correct_mapping": <True/False>, "decreases_severity": <True/False>, "reason": "<brief explanation>"}}`
        
        Context:
        A code smell was removed at a commit in the following file:
        - File: {smell_file_name}
        {f"- Method: {smell_method} (Lines {smell_method_range[0]} - {smell_method_range[1]})" if smell_method else ""}
        - Smell Kind: {smell_kind}
        - Smell Type: {smell_type}
        - Smell Cause: {smell_cause}

        In the same commit, a refactoring was applied:
        - Refactoring Type: {ref_type}
        - Description: {ref_description}
        - Code changes in a commit because of refactoring:
          - Before: {ref_left_changes}
          - After: {ref_right_changes}
        """.strip()
        
        return prompt
    
    def _get_file_name(self, package, type):
        if package == "<All packages>":
            return package
        slash_pkg_path = package.replace('.', '/') if package else ''
        extension = f"{type}.java" if type else ''
        return f"{slash_pkg_path}/{extension}" if slash_pkg_path and extension else ''
        
    def query_model(self, prompt):
        """
        Query the model with the generated prompt.
        """
        completion = self.client.chat.completions.create(
            model=self.model_config.MODEL,
            messages=[{"role": self.role, "content": prompt}],
            temperature=0.3
        )
        return completion.choices[0].message.content.strip()
    
SAMPLE_1 = {
    "repo_full_name": "litemall@linlinjava",
    "branch": "master",
    "smell_versions": [
      {
        "package_name": "org.linlinjava.litemall.admin.web",
        "type_name": "AdminCollectController",
        "method_name": "list",
        "method_start_ln": 24,
        "method_end_ln": 40,
        "smell_kind": "Implementation",
        "smell_name": "Long Parameter List",
        "cause": "The method has 7 parameters. "
      },
      {
        "package_name": "org.linlinjava.litemall.admin.web",
        "type_name": "AdminCollectController",
        "method_name": "list",
        "method_start_ln": 29,
        "method_end_ln": 46,
        "smell_kind": "Implementation",
        "smell_name": "Long Parameter List",
        "cause": "The method has 7 parameters. "
      },
      {
        "package_name": "org.linlinjava.litemall.admin.web",
        "type_name": "AdminCollectController",
        "method_name": "list",
        "method_start_ln": 31,
        "method_end_ln": 48,
        "smell_kind": "Implementation",
        "smell_name": "Long Parameter List",
        "cause": "The method has 7 parameters. "
      }
    ],
    "commit_versions": [
      {
        "commit_hash": "ad642a757f036fcdaaa8d2b0916aa14c1e9ceac6",
        "datetime": "2018-05-15T19:33:18+08:00"
      },
      {
        "commit_hash": "2072babd2a0bc0f8065209e172d24c1e6c39182f",
        "datetime": "2018-07-31T14:28:55+08:00"
      },
      {
        "commit_hash": "a5c2aff47d2ecb374afc91401486cb8b219a2e45",
        "datetime": "2018-11-16T21:44:11+08:00"
      },
      {
        "commit_hash": "835fd6f80b5fdce23b9f4548d40cbca20e65c895",
        "datetime": "2019-01-01T15:02:46+08:00"
      }
    ],
    "is_alive": False,
    "commit_span": 445,
    "days_span": 230,
    "removed_by_refactorings": [
      {
        "url": "https://github.com/linlinjava/litemall/commit/835fd6f80b5fdce23b9f4548d40cbca20e65c895",
        "type_name": "Remove Parameter",
        "description": "Remove Parameter adminId : Integer in method public list(adminId Integer, userId String, valueId String, page Integer, limit Integer, sort String, order String) : Object from class org.linlinjava.litemall.admin.web.AdminCollectController",
        "commit_hash": "835fd6f80b5fdce23b9f4548d40cbca20e65c895",
        "left_changes": [
          {
            "file_path": "litemall-admin-api/src/main/java/org/linlinjava/litemall/admin/web/AdminCollectController.java",
            "range": [
              32,
              32
            ],
            "code_element_type": "SINGLE_VARIABLE_DECLARATION",
            "code_element": "adminId : Integer",
            "description": "removed parameter"
          },
          {
            "file_path": "litemall-admin-api/src/main/java/org/linlinjava/litemall/admin/web/AdminCollectController.java",
            "range": [
              31,
              45
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "public list(adminId Integer, userId String, valueId String, page Integer, limit Integer, sort String, order String) : Object",
            "description": "original method declaration"
          }
        ],
        "right_changes": [
          {
            "file_path": "litemall-admin-api/src/main/java/org/linlinjava/litemall/admin/web/AdminCollectController.java",
            "range": [
              32,
              46
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "public list(userId String, valueId String, page Integer, limit Integer, sort String, order String) : Object",
            "description": "method declaration with removed parameter"
          }
        ]
      }
    ]
  }

SAMPLE_2 = {
    "repo_full_name": "powerjob@powerjob",
    "branch": "master",
    "smell_versions": [
      {
        "package_name": "com.github.kfcfans.oms.server.common.utils",
        "type_name": "CronExpression",
        "method_name": "addToSet",
        "method_start_ln": 949,
        "method_end_ln": 1079,
        "smell_kind": "Implementation",
        "smell_name": "Complex Conditional",
        "cause": "The conditional expression (val < 0 || val > 23 || end > 23) && (val != ALL_SPEC_INT) is complex."
      }
    ],
    "commit_versions": [
      {
        "commit_hash": "f1b3edea62ab4c26b55906814a248d5151f72a4b",
        "datetime": "2020-04-06T16:36:03+08:00"
      },
      {
        "commit_hash": "4295ff9a2db6a35e4158a892513dc48029c3a41e",
        "datetime": "2020-05-15T18:53:02+08:00"
      }
    ],
    "is_alive": False,
    "commit_span": 80,
    "days_span": 39,
    "removed_by_refactorings": [
        {
        "url": "https://github.com/powerjob/powerjob/commit/4295ff9a2db6a35e4158a892513dc48029c3a41e",
        "type_name": "Rename Package",
        "description": "Rename Package com.github.kfcfans.oms.server to com.github.kfcfans.oms.samples",
        "commit_hash": "4295ff9a2db6a35e4158a892513dc48029c3a41e",
        "left_changes": [
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/OhMyApplication.java",
            "range": [
              8,
              27
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.OhMyApplication",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/akka/OhMyServer.java",
            "range": [
              19,
              71
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.akka.OhMyServer",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/akka/actors/FriendActor.java",
            "range": [
              13,
              45
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.akka.actors.FriendActor",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/akka/actors/ServerActor.java",
            "range": [
              15,
              64
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.akka.actors.ServerActor",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/akka/requests/FriendQueryWorkerClusterStatusReq.java",
            "range": [
              9,
              20
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.akka.requests.FriendQueryWorkerClusterStatusReq",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/akka/requests/Ping.java",
            "range": [
              7,
              16
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.akka.requests.Ping",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/common/config/SwaggerConfig.java",
            "range": [
              13,
              43
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.common.config.SwaggerConfig",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/common/config/ThreadPoolConfig.java",
            "range": [
              12,
              53
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.common.config.ThreadPoolConfig",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/common/config/WebConfig.java",
            "range": [
              7,
              20
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.common.config.WebConfig",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/common/constans/ContainerSourceType.java",
            "range": [
              6,
              30
            ],
            "code_element_type": "ENUM_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.common.constans.ContainerSourceType",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/common/constans/ContainerStatus.java",
            "range": [
              6,
              30
            ],
            "code_element_type": "ENUM_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.common.constans.ContainerStatus",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/common/constans/JobStatus.java",
            "range": [
              6,
              30
            ],
            "code_element_type": "ENUM_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.common.constans.JobStatus",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/common/utils/CronExpression.java",
            "range": [
              16,
              1642
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.common.utils.CronExpression",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/common/utils/CronExpression.java",
            "range": [
              1644,
              1647
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.common.utils.ValueSet",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/common/utils/OmsFilePathUtils.java",
            "range": [
              6,
              60
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.common.utils.OmsFilePathUtils",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/common/utils/SpringUtils.java",
            "range": [
              8,
              31
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.common.utils.SpringUtils",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/common/utils/timewheel/HashedWheelTimer.java",
            "range": [
              15,
              335
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.common.utils.timewheel.HashedWheelTimer",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/common/utils/timewheel/Timer.java",
            "range": [
              6,
              23
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.common.utils.timewheel.Timer",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/common/utils/timewheel/TimerFuture.java",
            "range": [
              3,
              48
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.common.utils.timewheel.TimerFuture",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/common/utils/timewheel/TimerTask.java",
            "range": [
              3,
              11
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.common.utils.timewheel.TimerTask",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/PageResult.java",
            "range": [
              10,
              47
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.PageResult",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/StringPage.java",
            "range": [
              7,
              37
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.StringPage",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/config/CoreJpaConfig.java",
            "range": [
              21,
              82
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.config.CoreJpaConfig",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/config/LocalJpaConfig.java",
            "range": [
              23,
              82
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.config.LocalJpaConfig",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/config/MultiDatasourceConfig.java",
            "range": [
              14,
              45
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.config.MultiDatasourceConfig",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/core/model/AppInfoDO.java",
            "range": [
              8,
              31
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.core.model.AppInfoDO",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/core/model/ContainerInfoDO.java",
            "range": [
              8,
              41
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.core.model.ContainerInfoDO",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/core/model/InstanceInfoDO.java",
            "range": [
              11,
              57
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.core.model.InstanceInfoDO",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/core/model/JobInfoDO.java",
            "range": [
              16,
              101
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.core.model.JobInfoDO",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/core/model/OmsLockDO.java",
            "range": [
              9,
              37
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.core.model.OmsLockDO",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/core/model/ServerInfoDO.java",
            "range": [
              9,
              38
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.core.model.ServerInfoDO",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/core/model/UserInfoDO.java",
            "range": [
              8,
              33
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.core.model.UserInfoDO",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/core/repository/AppInfoRepository.java",
            "range": [
              8,
              25
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.core.repository.AppInfoRepository",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/core/repository/ContainerInfoRepository.java",
            "range": [
              8,
              18
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.core.repository.ContainerInfoRepository",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/core/repository/InstanceInfoRepository.java",
            "range": [
              15,
              77
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.core.repository.InstanceInfoRepository",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/core/repository/JobInfoRepository.java",
            "range": [
              11,
              33
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.core.repository.JobInfoRepository",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/core/repository/OmsLockRepository.java",
            "range": [
              11,
              30
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.core.repository.OmsLockRepository",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/core/repository/ServerInfoRepository.java",
            "range": [
              6,
              14
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.core.repository.ServerInfoRepository",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/core/repository/UserInfoRepository.java",
            "range": [
              8,
              19
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.core.repository.UserInfoRepository",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/local/LocalInstanceLogDO.java",
            "range": [
              9,
              42
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.local.LocalInstanceLogDO",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/local/LocalInstanceLogRepository.java",
            "range": [
              11,
              31
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.local.LocalInstanceLogRepository",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/persistence/mongodb/InstanceLogMetadata.java",
            "range": [
              5,
              27
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.persistence.mongodb.InstanceLogMetadata",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/CacheService.java",
            "range": [
              16,
              101
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.CacheService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/DispatchService.java",
            "range": [
              27,
              136
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.DispatchService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/JobService.java",
            "range": [
              26,
              208
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.JobService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/alarm/AlarmContent.java",
            "range": [
              5,
              46
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.alarm.AlarmContent",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/alarm/Alarmable.java",
            "range": [
              7,
              16
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.alarm.Alarmable",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/alarm/DefaultMailAlarmService.java",
            "range": [
              15,
              57
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.alarm.DefaultMailAlarmService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/alarm/OmsCenterAlarmService.java",
            "range": [
              16,
              61
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.alarm.OmsCenterAlarmService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/ha/ClusterStatusHolder.java",
            "range": [
              12,
              106
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.ha.ClusterStatusHolder",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/ha/ServerSelectService.java",
            "range": [
              24,
              130
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.ha.ServerSelectService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/ha/WorkerManagerService.java",
            "range": [
              11,
              81
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.ha.WorkerManagerService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/id/IdGenerateService.java",
            "range": [
              10,
              51
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.id.IdGenerateService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/id/SnowFlakeIdGenerator.java",
            "range": [
              3,
              93
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.id.SnowFlakeIdGenerator",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/instance/InstanceManager.java",
            "range": [
              28,
              240
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.instance.InstanceManager",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/instance/InstanceService.java",
            "range": [
              29,
              166
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.instance.InstanceService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/instance/InstanceStatusHolder.java",
            "range": [
              5,
              29
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.instance.InstanceStatusHolder",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/lock/DatabaseLockService.java",
            "range": [
              18,
              99
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.lock.DatabaseLockService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/lock/LockService.java",
            "range": [
              5,
              29
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.lock.LockService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/log/InstanceLogCleanService.java",
            "range": [
              20,
              110
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.log.InstanceLogCleanService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/log/InstanceLogService.java",
            "range": [
              38,
              373
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.log.InstanceLogService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/timing/InstanceStatusCheckService.java",
            "range": [
              29,
              152
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.timing.InstanceStatusCheckService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/timing/schedule/HashedWheelTimerHolder.java",
            "range": [
              5,
              17
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.timing.schedule.HashedWheelTimerHolder",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/service/timing/schedule/JobScheduleService.java",
            "range": [
              37,
              219
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.service.timing.schedule.JobScheduleService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/ControllerExceptionHandler.java",
            "range": [
              9,
              31
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.ControllerExceptionHandler",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/controller/AppInfoController.java",
            "range": [
              19,
              81
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.controller.AppInfoController",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/controller/ContainerController.java",
            "range": [
              30,
              152
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.controller.ContainerController",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/controller/InstanceController.java",
            "range": [
              35,
              188
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.controller.InstanceController",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/controller/JobController.java",
            "range": [
              30,
              145
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.controller.JobController",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/controller/OpenAPIController.java",
            "range": [
              19,
              131
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.controller.OpenAPIController",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/controller/ServerController.java",
            "range": [
              14,
              50
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.controller.ServerController",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/controller/SystemInfoController.java",
            "range": [
              33,
              109
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.controller.SystemInfoController",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/controller/UserInfoController.java",
            "range": [
              21,
              70
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.controller.UserInfoController",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/request/GenerateContainerTemplateRequest.java",
            "range": [
              5,
              25
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.request.GenerateContainerTemplateRequest",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/request/ModifyAppInfoRequest.java",
            "range": [
              5,
              17
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.request.ModifyAppInfoRequest",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/request/ModifyUserInfoRequest.java",
            "range": [
              5,
              23
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.request.ModifyUserInfoRequest",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/request/QueryInstanceRequest.java",
            "range": [
              5,
              24
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.request.QueryInstanceRequest",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/request/QueryJobInfoRequest.java",
            "range": [
              5,
              24
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.request.QueryJobInfoRequest",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/request/SaveContainerInfoRequest.java",
            "range": [
              7,
              32
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.request.SaveContainerInfoRequest",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/response/ContainerInfoVO.java",
            "range": [
              7,
              35
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.response.ContainerInfoVO",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/response/InstanceLogVO.java",
            "range": [
              7,
              39
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.response.InstanceLogVO",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/response/JobInfoVO.java",
            "range": [
              8,
              79
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.response.JobInfoVO",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/response/SystemOverviewVO.java",
            "range": [
              5,
              16
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.response.SystemOverviewVO",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/server/web/response/WorkerStatusVO.java",
            "range": [
              9,
              61
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.web.response.WorkerStatusVO",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/test/java/com/github/kfcfans/oms/server/test/OmsLogTest.java",
            "range": [
              19,
              58
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.test.OmsLogTest",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/test/java/com/github/kfcfans/oms/server/test/RepositoryTest.java",
            "range": [
              22,
              76
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.test.RepositoryTest",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/test/java/com/github/kfcfans/oms/server/test/ServiceTest.java",
            "range": [
              15,
              58
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.test.ServiceTest",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/test/java/com/github/kfcfans/oms/server/test/UtilsTest.java",
            "range": [
              15,
              80
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.test.UtilsTest",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/server/MysteryService.java",
            "range": [
              5,
              18
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.MysteryService",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/server/OhMySchedulerConfig.java",
            "range": [
              12,
              39
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.OhMySchedulerConfig",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/server/SampleApplication.java",
            "range": [
              7,
              19
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.SampleApplication",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/server/mr/DAGSimulationProcessor.java",
            "range": [
              11,
              70
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.mr.DAGSimulationProcessor",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/server/processors/BroadcastProcessorDemo.java",
            "range": [
              14,
              54
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.processors.BroadcastProcessorDemo",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/server/processors/MapProcessorDemo.java",
            "range": [
              18,
              71
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.processors.MapProcessorDemo",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/server/processors/MapReduceProcessorDemo.java",
            "range": [
              22,
              95
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.processors.MapReduceProcessorDemo",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/server/processors/StandaloneProcessorDemo.java",
            "range": [
              12,
              44
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.processors.StandaloneProcessorDemo",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/server/processors/TimeoutProcessor.java",
            "range": [
              8,
              21
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.processors.TimeoutProcessor",
            "description": "original type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/server/tester/OmsLogPerformanceTester.java",
            "range": [
              10,
              52
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.server.tester.OmsLogPerformanceTester",
            "description": "original type declaration"
          }
        ],
        "right_changes": [
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/OhMyApplication.java",
            "range": [
              8,
              27
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.OhMyApplication",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/akka/OhMyServer.java",
            "range": [
              19,
              71
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.akka.OhMyServer",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/akka/actors/FriendActor.java",
            "range": [
              13,
              45
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.akka.actors.FriendActor",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/akka/actors/ServerActor.java",
            "range": [
              15,
              64
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.akka.actors.ServerActor",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/akka/requests/FriendQueryWorkerClusterStatusReq.java",
            "range": [
              9,
              20
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.akka.requests.FriendQueryWorkerClusterStatusReq",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/akka/requests/Ping.java",
            "range": [
              7,
              16
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.akka.requests.Ping",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/common/config/SwaggerConfig.java",
            "range": [
              13,
              43
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.common.config.SwaggerConfig",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/common/config/ThreadPoolConfig.java",
            "range": [
              12,
              53
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.common.config.ThreadPoolConfig",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/common/config/WebConfig.java",
            "range": [
              7,
              20
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.common.config.WebConfig",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/common/constans/ContainerSourceType.java",
            "range": [
              6,
              30
            ],
            "code_element_type": "ENUM_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.common.constans.ContainerSourceType",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/common/constans/ContainerStatus.java",
            "range": [
              6,
              30
            ],
            "code_element_type": "ENUM_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.common.constans.ContainerStatus",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/common/constans/JobStatus.java",
            "range": [
              6,
              30
            ],
            "code_element_type": "ENUM_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.common.constans.JobStatus",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/common/utils/CronExpression.java",
            "range": [
              16,
              1642
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.common.utils.CronExpression",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/common/utils/CronExpression.java",
            "range": [
              1644,
              1647
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.common.utils.ValueSet",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/common/utils/OmsFilePathUtils.java",
            "range": [
              5,
              59
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.common.utils.OmsFilePathUtils",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/common/utils/SpringUtils.java",
            "range": [
              8,
              31
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.common.utils.SpringUtils",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/common/utils/timewheel/HashedWheelTimer.java",
            "range": [
              15,
              335
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.common.utils.timewheel.HashedWheelTimer",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/common/utils/timewheel/Timer.java",
            "range": [
              6,
              23
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.common.utils.timewheel.Timer",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/common/utils/timewheel/TimerFuture.java",
            "range": [
              3,
              48
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.common.utils.timewheel.TimerFuture",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/common/utils/timewheel/TimerTask.java",
            "range": [
              3,
              11
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.common.utils.timewheel.TimerTask",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/PageResult.java",
            "range": [
              10,
              47
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.PageResult",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/StringPage.java",
            "range": [
              7,
              37
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.StringPage",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/config/CoreJpaConfig.java",
            "range": [
              21,
              82
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.config.CoreJpaConfig",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/config/LocalJpaConfig.java",
            "range": [
              23,
              82
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.config.LocalJpaConfig",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/config/MultiDatasourceConfig.java",
            "range": [
              13,
              44
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.config.MultiDatasourceConfig",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/core/model/AppInfoDO.java",
            "range": [
              8,
              31
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.core.model.AppInfoDO",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/core/model/ContainerInfoDO.java",
            "range": [
              8,
              41
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.core.model.ContainerInfoDO",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/core/model/InstanceInfoDO.java",
            "range": [
              11,
              57
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.core.model.InstanceInfoDO",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/core/model/JobInfoDO.java",
            "range": [
              16,
              101
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.core.model.JobInfoDO",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/core/model/OmsLockDO.java",
            "range": [
              9,
              37
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.core.model.OmsLockDO",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/core/model/ServerInfoDO.java",
            "range": [
              9,
              38
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.core.model.ServerInfoDO",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/core/model/UserInfoDO.java",
            "range": [
              8,
              33
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.core.model.UserInfoDO",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/core/repository/AppInfoRepository.java",
            "range": [
              8,
              25
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.core.repository.AppInfoRepository",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/core/repository/ContainerInfoRepository.java",
            "range": [
              8,
              18
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.core.repository.ContainerInfoRepository",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/core/repository/InstanceInfoRepository.java",
            "range": [
              15,
              77
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.core.repository.InstanceInfoRepository",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/core/repository/JobInfoRepository.java",
            "range": [
              11,
              33
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.core.repository.JobInfoRepository",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/core/repository/OmsLockRepository.java",
            "range": [
              11,
              30
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.core.repository.OmsLockRepository",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/core/repository/ServerInfoRepository.java",
            "range": [
              6,
              14
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.core.repository.ServerInfoRepository",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/core/repository/UserInfoRepository.java",
            "range": [
              8,
              19
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.core.repository.UserInfoRepository",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/local/LocalInstanceLogDO.java",
            "range": [
              9,
              42
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.local.LocalInstanceLogDO",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/local/LocalInstanceLogRepository.java",
            "range": [
              11,
              31
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.local.LocalInstanceLogRepository",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/persistence/mongodb/InstanceLogMetadata.java",
            "range": [
              5,
              27
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.persistence.mongodb.InstanceLogMetadata",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/CacheService.java",
            "range": [
              16,
              101
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.CacheService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/DispatchService.java",
            "range": [
              27,
              136
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.DispatchService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/JobService.java",
            "range": [
              26,
              208
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.JobService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/alarm/AlarmContent.java",
            "range": [
              5,
              46
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.alarm.AlarmContent",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/alarm/Alarmable.java",
            "range": [
              7,
              16
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.alarm.Alarmable",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/alarm/DefaultMailAlarmService.java",
            "range": [
              15,
              57
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.alarm.DefaultMailAlarmService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/alarm/OmsCenterAlarmService.java",
            "range": [
              16,
              61
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.alarm.OmsCenterAlarmService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/ha/ClusterStatusHolder.java",
            "range": [
              12,
              106
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.ha.ClusterStatusHolder",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/ha/ServerSelectService.java",
            "range": [
              24,
              130
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.ha.ServerSelectService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/ha/WorkerManagerService.java",
            "range": [
              11,
              81
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.ha.WorkerManagerService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/id/IdGenerateService.java",
            "range": [
              10,
              51
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.id.IdGenerateService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/id/SnowFlakeIdGenerator.java",
            "range": [
              3,
              93
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.id.SnowFlakeIdGenerator",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/instance/InstanceManager.java",
            "range": [
              28,
              240
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.instance.InstanceManager",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/instance/InstanceService.java",
            "range": [
              29,
              166
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.instance.InstanceService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/instance/InstanceStatusHolder.java",
            "range": [
              5,
              29
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.instance.InstanceStatusHolder",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/lock/DatabaseLockService.java",
            "range": [
              18,
              99
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.lock.DatabaseLockService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/lock/LockService.java",
            "range": [
              5,
              29
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.lock.LockService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/log/InstanceLogCleanService.java",
            "range": [
              20,
              110
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.log.InstanceLogCleanService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/log/InstanceLogService.java",
            "range": [
              38,
              373
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.log.InstanceLogService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/timing/InstanceStatusCheckService.java",
            "range": [
              29,
              152
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.timing.InstanceStatusCheckService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/timing/schedule/HashedWheelTimerHolder.java",
            "range": [
              5,
              17
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.timing.schedule.HashedWheelTimerHolder",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/service/timing/schedule/JobScheduleService.java",
            "range": [
              37,
              219
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.service.timing.schedule.JobScheduleService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/ControllerExceptionHandler.java",
            "range": [
              9,
              31
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.ControllerExceptionHandler",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/controller/AppInfoController.java",
            "range": [
              19,
              81
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.controller.AppInfoController",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/controller/ContainerController.java",
            "range": [
              30,
              153
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.controller.ContainerController",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/controller/InstanceController.java",
            "range": [
              35,
              188
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.controller.InstanceController",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/controller/JobController.java",
            "range": [
              30,
              145
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.controller.JobController",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/controller/OpenAPIController.java",
            "range": [
              18,
              130
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.controller.OpenAPIController",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/controller/ServerController.java",
            "range": [
              14,
              50
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.controller.ServerController",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/controller/SystemInfoController.java",
            "range": [
              33,
              109
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.controller.SystemInfoController",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/controller/UserInfoController.java",
            "range": [
              21,
              70
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.controller.UserInfoController",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/request/GenerateContainerTemplateRequest.java",
            "range": [
              5,
              25
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.request.GenerateContainerTemplateRequest",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/request/ModifyAppInfoRequest.java",
            "range": [
              5,
              17
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.request.ModifyAppInfoRequest",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/request/ModifyUserInfoRequest.java",
            "range": [
              5,
              23
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.request.ModifyUserInfoRequest",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/request/QueryInstanceRequest.java",
            "range": [
              5,
              24
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.request.QueryInstanceRequest",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/request/QueryJobInfoRequest.java",
            "range": [
              5,
              24
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.request.QueryJobInfoRequest",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/request/SaveContainerInfoRequest.java",
            "range": [
              7,
              32
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.request.SaveContainerInfoRequest",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/response/ContainerInfoVO.java",
            "range": [
              7,
              35
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.response.ContainerInfoVO",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/response/InstanceLogVO.java",
            "range": [
              5,
              37
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.response.InstanceLogVO",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/response/JobInfoVO.java",
            "range": [
              8,
              79
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.response.JobInfoVO",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/response/SystemOverviewVO.java",
            "range": [
              5,
              16
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.response.SystemOverviewVO",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/main/java/com/github/kfcfans/oms/samples/web/response/WorkerStatusVO.java",
            "range": [
              9,
              61
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.web.response.WorkerStatusVO",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/test/java/com/github/kfcfans/oms/samples/test/OmsLogTest.java",
            "range": [
              19,
              58
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.test.OmsLogTest",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/test/java/com/github/kfcfans/oms/samples/test/RepositoryTest.java",
            "range": [
              22,
              76
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.test.RepositoryTest",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/test/java/com/github/kfcfans/oms/samples/test/ServiceTest.java",
            "range": [
              15,
              58
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.test.ServiceTest",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-server/src/test/java/com/github/kfcfans/oms/samples/test/UtilsTest.java",
            "range": [
              15,
              80
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.test.UtilsTest",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/samples/MysteryService.java",
            "range": [
              5,
              18
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.MysteryService",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/samples/OhMySchedulerConfig.java",
            "range": [
              12,
              39
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.OhMySchedulerConfig",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/samples/SampleApplication.java",
            "range": [
              7,
              19
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.SampleApplication",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/samples/mr/DAGSimulationProcessor.java",
            "range": [
              11,
              70
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.mr.DAGSimulationProcessor",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/samples/processors/BroadcastProcessorDemo.java",
            "range": [
              14,
              54
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.processors.BroadcastProcessorDemo",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/samples/processors/MapProcessorDemo.java",
            "range": [
              18,
              71
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.processors.MapProcessorDemo",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/samples/processors/MapReduceProcessorDemo.java",
            "range": [
              22,
              95
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.processors.MapReduceProcessorDemo",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/samples/processors/StandaloneProcessorDemo.java",
            "range": [
              12,
              44
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.processors.StandaloneProcessorDemo",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/samples/processors/TimeoutProcessor.java",
            "range": [
              8,
              21
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.processors.TimeoutProcessor",
            "description": "moved type declaration"
          },
          {
            "file_path": "oh-my-scheduler-worker-samples/src/main/java/com/github/kfcfans/oms/samples/tester/OmsLogPerformanceTester.java",
            "range": [
              10,
              52
            ],
            "code_element_type": "TYPE_DECLARATION",
            "code_element": "com.github.kfcfans.oms.samples.tester.OmsLogPerformanceTester",
            "description": "moved type declaration"
          }
        ]
        }
    ]
  }

SAMPLE_3 = {
    "repo_full_name": "cryptomator@cryptomator",
    "branch": "develop",
    "smell_versions": [
      {
        "package_name": "org.cryptomator.launcher",
        "type_name": "Cryptomator",
        "method_name": None,
        "method_start_ln": None,
        "method_end_ln": None,
        "smell_kind": "Design",
        "smell_name": "Feature Envy",
        "cause": "The tool detected a instance of this smell because main is more interested in members of the type: CryptomatorComponent"
      }
    ],
    "commit_versions": [
      {
        "commit_hash": "8814372c68a75b9190ac4b4758a3366dfbd2efee",
        "datetime": "2019-02-20T23:28:33+01:00"
      },
      {
        "commit_hash": "dd3c969f0f409b5b075862b9eddead4b101faa4a",
        "datetime": "2019-02-26T22:41:33+01:00"
      }
    ],
    "is_alive": False,
    "commit_span": 21,
    "days_span": 5,
    "removed_by_refactorings": [
      {
        "url": "https://github.com/cryptomator/cryptomator/commit/dd3c969f0f409b5b075862b9eddead4b101faa4a",
        "type_name": "Extract Method",
        "description": "Extract Method private sendArgsToRunningInstance(args String[]) : boolean extracted from public main(args String[]) : void in class org.cryptomator.launcher.Cryptomator",
        "commit_hash": "dd3c969f0f409b5b075862b9eddead4b101faa4a",
        "left_changes": [
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              30,
              50
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "public main(args String[]) : void",
            "description": "source method declaration before extraction"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              34,
              34
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "extracted code from source method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              43,
              43
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "extracted code from source method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              42,
              45
            ],
            "code_element_type": "CATCH_CLAUSE",
            "code_element": None,
            "description": "extracted code from source method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              35,
              35
            ],
            "code_element_type": "IF_STATEMENT_CONDITION",
            "code_element": None,
            "description": "extracted code from source method declaration"
          }
        ],
        "right_changes": [
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              74,
              89
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "private sendArgsToRunningInstance(args String[]) : boolean",
            "description": "extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              83,
              83
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              86,
              86
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              85,
              88
            ],
            "code_element_type": "CATCH_CLAUSE",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              84,
              84
            ],
            "code_element_type": "RETURN_STATEMENT",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              50,
              72
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "private run(args String[]) : int",
            "description": "source method declaration after extraction"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              59,
              59
            ],
            "code_element_type": "METHOD_INVOCATION",
            "code_element": "sendArgsToRunningInstance(args)",
            "description": "extracted method invocation"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              87,
              87
            ],
            "code_element_type": "RETURN_STATEMENT",
            "code_element": None,
            "description": "added statement in extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              82,
              88
            ],
            "code_element_type": "TRY_STATEMENT",
            "code_element": None,
            "description": "added statement in extracted method declaration"
          }
        ]
      },
      {
        "url": "https://github.com/cryptomator/cryptomator/commit/dd3c969f0f409b5b075862b9eddead4b101faa4a",
        "type_name": "Extract Method",
        "description": "Extract Method private runGuiApplication() : void extracted from public main(args String[]) : void in class org.cryptomator.launcher.Cryptomator",
        "commit_hash": "dd3c969f0f409b5b075862b9eddead4b101faa4a",
        "left_changes": [
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              30,
              50
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "public main(args String[]) : void",
            "description": "source method declaration before extraction"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              39,
              39
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "extracted code from source method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              38,
              38
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "extracted code from source method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              33,
              48
            ],
            "code_element_type": "TRY_STATEMENT",
            "code_element": None,
            "description": "extracted code from source method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              45,
              48
            ],
            "code_element_type": "CATCH_CLAUSE",
            "code_element": None,
            "description": "extracted code from source method declaration"
          }
        ],
        "right_changes": [
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              91,
              109
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "private runGuiApplication() : void",
            "description": "extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              99,
              99
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              98,
              98
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              97,
              108
            ],
            "code_element_type": "TRY_STATEMENT",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              106,
              108
            ],
            "code_element_type": "CATCH_CLAUSE",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              50,
              72
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "private run(args String[]) : int",
            "description": "source method declaration after extraction"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              65,
              65
            ],
            "code_element_type": "METHOD_INVOCATION",
            "code_element": "runGuiApplication()",
            "description": "extracted method invocation"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              100,
              104
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "added statement in extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              105,
              105
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "added statement in extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              107,
              107
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "added statement in extracted method declaration"
          }
        ]
      },
      {
        "url": "https://github.com/cryptomator/cryptomator/commit/dd3c969f0f409b5b075862b9eddead4b101faa4a",
        "type_name": "Extract Method",
        "description": "Extract Method private run(args String[]) : int extracted from public main(args String[]) : void in class org.cryptomator.launcher.Cryptomator",
        "commit_hash": "dd3c969f0f409b5b075862b9eddead4b101faa4a",
        "left_changes": [
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              30,
              50
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "public main(args String[]) : void",
            "description": "source method declaration before extraction"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              31,
              31
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "extracted code from source method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              36,
              36
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "extracted code from source method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              47,
              47
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "extracted code from source method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              47,
              47
            ],
            "code_element_type": "NUMBER_LITERAL",
            "code_element": None,
            "description": "extracted code from source method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              35,
              41
            ],
            "code_element_type": "IF_STATEMENT",
            "code_element": None,
            "description": "extracted code from source method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              35,
              37
            ],
            "code_element_type": "BLOCK",
            "code_element": None,
            "description": "extracted code from source method declaration"
          }
        ],
        "right_changes": [
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              50,
              72
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "private run(args String[]) : int",
            "description": "extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              57,
              57
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              60,
              60
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              70,
              70
            ],
            "code_element_type": "RETURN_STATEMENT",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              70,
              70
            ],
            "code_element_type": "NUMBER_LITERAL",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              59,
              62
            ],
            "code_element_type": "IF_STATEMENT",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              59,
              62
            ],
            "code_element_type": "BLOCK",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              45,
              48
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "public main(args String[]) : void",
            "description": "source method declaration after extraction"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              46,
              46
            ],
            "code_element_type": "METHOD_INVOCATION",
            "code_element": "CRYPTOMATOR_COMPONENT.application().run(args)",
            "description": "extracted method invocation"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              56,
              56
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "added statement in extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              65,
              65
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "added statement in extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              66,
              66
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "added statement in extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              67,
              67
            ],
            "code_element_type": "RETURN_STATEMENT",
            "code_element": None,
            "description": "added statement in extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              61,
              61
            ],
            "code_element_type": "RETURN_STATEMENT",
            "code_element": None,
            "description": "added statement in extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              69,
              69
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "added statement in extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              64,
              71
            ],
            "code_element_type": "TRY_STATEMENT",
            "code_element": None,
            "description": "added statement in extracted method declaration"
          },
          {
            "file_path": "main/launcher/src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              68,
              71
            ],
            "code_element_type": "CATCH_CLAUSE",
            "code_element": None,
            "description": "added statement in extracted method declaration"
          }
        ]
      }
    ]
  }

SAMPLE_4 = {
    "repo_full_name": "easyexcel@alibaba",
    "branch": "master",
    "is_the_map_correct?": True,
    "reason_for_incorrect_mapping?": "CHANGED_SMELL_SEVERITY, DECREASED_SEVERITY",
    "smell_versions": [
      {
        "package_name": "com.alibaba.excel.write.metadata.holder",
        "type_name": "WriteWorkbookHolder",
        "method_name": "setHasBeenInitializedSheetNameMap",
        "method_start_ln": 218,
        "method_end_ln": 223,
        "smell_kind": "Implementation",
        "smell_name": "Long Identifier",
        "cause": "The length of the field hasBeenInitializedSheetNameMap is 30."
      }
    ],
    "commit_versions": [
      {
        "commit_hash": "3b89f724dd45bbeb864ce8a93cd88cdfec32c558",
        "datetime": "2021-04-15T17:26:45+08:00"
      },
      {
        "commit_hash": "74562ee5c9e1e8d0906b400467f8bd8a0906c9f8",
        "datetime": "2021-04-22T21:49:39+08:00"
      }
    ],
    "is_alive": False,
    "commit_span": 10,
    "days_span": 7,
    "removed_by_refactorings": [
      {
        "url": "https://github.com/alibaba/easyexcel/commit/74562ee5c9e1e8d0906b400467f8bd8a0906c9f8",
        "type_name": "Change Variable Type",
        "description": "Change Variable Type dataFormat : Short to dataFormat : DataFormatData in method public getDataFormat(format String) : DataFormatData from class com.alibaba.excel.write.metadata.holder.WriteWorkbookHolder",
        "commit_hash": "74562ee5c9e1e8d0906b400467f8bd8a0906c9f8",
        "left_changes": [
          {
            "file_path": "src/main/java/com/alibaba/excel/write/metadata/holder/WriteWorkbookHolder.java",
            "range": [
              217,
              217
            ],
            "code_element_type": "VARIABLE_DECLARATION_STATEMENT",
            "code_element": "dataFormat : Short",
            "description": "original variable declaration"
          },
          {
            "file_path": "src/main/java/com/alibaba/excel/write/metadata/holder/WriteWorkbookHolder.java",
            "range": [
              219,
              219
            ],
            "code_element_type": "RETURN_STATEMENT",
            "code_element": None,
            "description": "statement referencing the original variable"
          },
          {
            "file_path": "src/main/java/com/alibaba/excel/write/metadata/holder/WriteWorkbookHolder.java",
            "range": [
              222,
              222
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "statement referencing the original variable"
          },
          {
            "file_path": "src/main/java/com/alibaba/excel/write/metadata/holder/WriteWorkbookHolder.java",
            "range": [
              223,
              223
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "statement referencing the original variable"
          },
          {
            "file_path": "src/main/java/com/alibaba/excel/write/metadata/holder/WriteWorkbookHolder.java",
            "range": [
              224,
              224
            ],
            "code_element_type": "RETURN_STATEMENT",
            "code_element": None,
            "description": "statement referencing the original variable"
          },
          {
            "file_path": "src/main/java/com/alibaba/excel/write/metadata/holder/WriteWorkbookHolder.java",
            "range": [
              218,
              220
            ],
            "code_element_type": "IF_STATEMENT",
            "code_element": None,
            "description": "statement referencing the original variable"
          }
        ],
        "right_changes": [
          {
            "file_path": "src/main/java/com/alibaba/excel/write/metadata/holder/WriteWorkbookHolder.java",
            "range": [
              218,
              218
            ],
            "code_element_type": "VARIABLE_DECLARATION_STATEMENT",
            "code_element": "dataFormat : DataFormatData",
            "description": "changed-type variable declaration"
          },
          {
            "file_path": "src/main/java/com/alibaba/excel/write/metadata/holder/WriteWorkbookHolder.java",
            "range": [
              220,
              220
            ],
            "code_element_type": "RETURN_STATEMENT",
            "code_element": None,
            "description": "statement referencing the variable with changed type"
          },
          {
            "file_path": "src/main/java/com/alibaba/excel/write/metadata/holder/WriteWorkbookHolder.java",
            "range": [
              223,
              223
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "statement referencing the variable with changed type"
          },
          {
            "file_path": "src/main/java/com/alibaba/excel/write/metadata/holder/WriteWorkbookHolder.java",
            "range": [
              224,
              224
            ],
            "code_element_type": "EXPRESSION_STATEMENT",
            "code_element": None,
            "description": "statement referencing the variable with changed type"
          },
          {
            "file_path": "src/main/java/com/alibaba/excel/write/metadata/holder/WriteWorkbookHolder.java",
            "range": [
              225,
              225
            ],
            "code_element_type": "RETURN_STATEMENT",
            "code_element": None,
            "description": "statement referencing the variable with changed type"
          },
          {
            "file_path": "src/main/java/com/alibaba/excel/write/metadata/holder/WriteWorkbookHolder.java",
            "range": [
              219,
              221
            ],
            "code_element_type": "IF_STATEMENT",
            "code_element": None,
            "description": "statement referencing the variable with changed type"
          }
        ]
      }
    ]
  }

SAMPLE_5 = {
    "repo_full_name": "aegis@beemdevelopment",
    "branch": "master",
    "is_the_map_correct?": True,
    "reason_for_incorrect_mapping?": "CHANGED_SMELL_SEVERITY, DECREASED_SEVERITY",
    "smell_versions": [
      {
        "package_name": "com.beemdevelopment.aegis.vault",
        "type_name": "VaultManager",
        "method_name": None,
        "method_start_ln": None,
        "method_end_ln": None,
        "smell_kind": "Design",
        "smell_name": "Insufficient Modularization",
        "cause": "The tool detected the smell in this class becuase the class has bloated interface (large number of public methods). Total public methods in the class: 26 public methods"
      }
    ],
    "commit_versions": [
      {
        "commit_hash": "f15a0018ef8b179790cc0b152be39edcfd994c8a",
        "datetime": "2020-12-03T21:48:48+01:00"
      },
      {
        "commit_hash": "4e198d2556858e36314cbf111125986b331b3564",
        "datetime": "2020-12-03T22:16:35+01:00"
      }
    ],
    "is_alive": False,
    "commit_span": 1,
    "days_span": 0,
    "removed_by_refactorings": [
      {
        "url": "https://github.com/beemdevelopment/aegis/commit/4e198d2556858e36314cbf111125986b331b3564",
        "type_name": "Extract Method",
        "description": "Extract Method private getAtomicFile(context Context) : AtomicFile extracted from public fileExists(context Context) : boolean in class com.beemdevelopment.aegis.vault.VaultManager",
        "commit_hash": "4e198d2556858e36314cbf111125986b331b3564",
        "left_changes": [
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              48,
              51
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "public fileExists(context Context) : boolean",
            "description": "source method declaration before extraction"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              49,
              49
            ],
            "code_element_type": "VARIABLE_DECLARATION_STATEMENT",
            "code_element": None,
            "description": "extracted code from source method declaration"
          }
        ],
        "right_changes": [
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              50,
              52
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "private getAtomicFile(context Context) : AtomicFile",
            "description": "extracted method declaration"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              51,
              51
            ],
            "code_element_type": "RETURN_STATEMENT",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              54,
              57
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "public fileExists(context Context) : boolean",
            "description": "source method declaration after extraction"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              55,
              55
            ],
            "code_element_type": "METHOD_INVOCATION",
            "code_element": "getAtomicFile(context)",
            "description": "extracted method invocation"
          }
        ]
      },
      {
        "url": "https://github.com/beemdevelopment/aegis/commit/4e198d2556858e36314cbf111125986b331b3564",
        "type_name": "Extract Method",
        "description": "Extract Method private getAtomicFile(context Context) : AtomicFile extracted from public deleteFile(context Context) : void in class com.beemdevelopment.aegis.vault.VaultManager",
        "commit_hash": "4e198d2556858e36314cbf111125986b331b3564",
        "left_changes": [
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              53,
              57
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "public deleteFile(context Context) : void",
            "description": "source method declaration before extraction"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              54,
              54
            ],
            "code_element_type": "VARIABLE_DECLARATION_STATEMENT",
            "code_element": None,
            "description": "extracted code from source method declaration"
          }
        ],
        "right_changes": [
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              50,
              52
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "private getAtomicFile(context Context) : AtomicFile",
            "description": "extracted method declaration"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              51,
              51
            ],
            "code_element_type": "RETURN_STATEMENT",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              59,
              61
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "public deleteFile(context Context) : void",
            "description": "source method declaration after extraction"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              60,
              60
            ],
            "code_element_type": "METHOD_INVOCATION",
            "code_element": "getAtomicFile(context)",
            "description": "extracted method invocation"
          }
        ]
      },
      {
        "url": "https://github.com/beemdevelopment/aegis/commit/4e198d2556858e36314cbf111125986b331b3564",
        "type_name": "Extract Method",
        "description": "Extract Method private getAtomicFile(context Context) : AtomicFile extracted from public readFile(context Context) : VaultFile in class com.beemdevelopment.aegis.vault.VaultManager",
        "commit_hash": "4e198d2556858e36314cbf111125986b331b3564",
        "left_changes": [
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              59,
              68
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "public readFile(context Context) : VaultFile",
            "description": "source method declaration before extraction"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              60,
              60
            ],
            "code_element_type": "VARIABLE_DECLARATION_STATEMENT",
            "code_element": None,
            "description": "extracted code from source method declaration"
          }
        ],
        "right_changes": [
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              50,
              52
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "private getAtomicFile(context Context) : AtomicFile",
            "description": "extracted method declaration"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              51,
              51
            ],
            "code_element_type": "RETURN_STATEMENT",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              63,
              72
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "public readFile(context Context) : VaultFile",
            "description": "source method declaration after extraction"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              64,
              64
            ],
            "code_element_type": "METHOD_INVOCATION",
            "code_element": "getAtomicFile(context)",
            "description": "extracted method invocation"
          }
        ]
      },
      {
        "url": "https://github.com/beemdevelopment/aegis/commit/4e198d2556858e36314cbf111125986b331b3564",
        "type_name": "Extract Method",
        "description": "Extract Method private getAtomicFile(context Context) : AtomicFile extracted from public save(context Context, vaultFile VaultFile) : void in class com.beemdevelopment.aegis.vault.VaultManager",
        "commit_hash": "4e198d2556858e36314cbf111125986b331b3564",
        "left_changes": [
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              92,
              107
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "public save(context Context, vaultFile VaultFile) : void",
            "description": "source method declaration before extraction"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              94,
              94
            ],
            "code_element_type": "VARIABLE_DECLARATION_STATEMENT",
            "code_element": None,
            "description": "extracted code from source method declaration"
          }
        ],
        "right_changes": [
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              50,
              52
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "private getAtomicFile(context Context) : AtomicFile",
            "description": "extracted method declaration"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              51,
              51
            ],
            "code_element_type": "RETURN_STATEMENT",
            "code_element": None,
            "description": "extracted code to extracted method declaration"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              96,
              111
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "public save(context Context, vaultFile VaultFile) : void",
            "description": "source method declaration after extraction"
          },
          {
            "file_path": "app/src/main/java/com/beemdevelopment/aegis/vault/VaultManager.java",
            "range": [
              98,
              98
            ],
            "code_element_type": "METHOD_INVOCATION",
            "code_element": "getAtomicFile(context)",
            "description": "extracted method invocation"
          }
        ]
      }
    ]
  }

SAMPLE_6 = {
    "repo_full_name": "cryptomator@cryptomator",
    "branch": "develop",
    "is_the_map_correct?": True,
    "reason_for_incorrect_mapping?": "SHOULD_NOT_RELATE_BY_DEFS, CHANGED_SMELL_SEVERITY, INCREASED_SEVERITY",
    "smell_versions": [
      {
        "package_name": "org.cryptomator.launcher",
        "type_name": "Cryptomator",
        "method_name": "Cryptomator",
        "method_start_ln": 41,
        "method_end_ln": 47,
        "smell_kind": "Implementation",
        "smell_name": "Long Parameter List",
        "cause": "The method has 5 parameters. "
      }
    ],
    "commit_versions": [
      {
        "commit_hash": "c7d1b9dbd670203e7644c734a7be5b3c3ce6e663",
        "datetime": "2022-03-31T16:32:17+02:00"
      },
      {
        "commit_hash": "71d346eddd8aae80ce84ba5c6aa804947087b8c1",
        "datetime": "2022-04-02T12:17:10+02:00"
      }
    ],
    "is_alive": False,
    "commit_span": 12,
    "days_span": 1,
    "removed_by_refactorings": [
      {
        "url": "https://github.com/cryptomator/cryptomator/commit/71d346eddd8aae80ce84ba5c6aa804947087b8c1",
        "type_name": "Add Parameter",
        "description": "Add Parameter supportedLanguages : SupportedLanguages in method package Cryptomator(logConfig LoggerConfiguration, debugMode DebugMode, supportedLanguages SupportedLanguages, env Environment, ipcMessageHandler Lazy<IpcMessageHandler>, shutdownHook ShutdownHook) from class org.cryptomator.launcher.Cryptomator",
        "commit_hash": "71d346eddd8aae80ce84ba5c6aa804947087b8c1",
        "left_changes": [
          {
            "file_path": "src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              41,
              48
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "package Cryptomator(logConfig LoggerConfiguration, debugMode DebugMode, env Environment, ipcMessageHandler Lazy<IpcMessageHandler>, shutdownHook ShutdownHook)",
            "description": "original method declaration"
          }
        ],
        "right_changes": [
          {
            "file_path": "src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              43,
              43
            ],
            "code_element_type": "SINGLE_VARIABLE_DECLARATION",
            "code_element": "supportedLanguages : SupportedLanguages",
            "description": "added parameter"
          },
          {
            "file_path": "src/main/java/org/cryptomator/launcher/Cryptomator.java",
            "range": [
              42,
              50
            ],
            "code_element_type": "METHOD_DECLARATION",
            "code_element": "package Cryptomator(logConfig LoggerConfiguration, debugMode DebugMode, supportedLanguages SupportedLanguages, env Environment, ipcMessageHandler Lazy<IpcMessageHandler>, shutdownHook ShutdownHook)",
            "description": "method declaration with added parameter"
          }
        ]
      }
    ]
  }

if __name__ == "__main__":
    analysis = LLMAnalysis(model_name="OpenAI")
    prompt = analysis.generate_prompt(SAMPLE_6)
    response = analysis.query_model(prompt)
    print("Prompt:\n" + prompt)
    print("\nResponse:" + response)
    