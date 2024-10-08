from django_logic import Process as BaseProcess, Transition, ProcessManager, Action
from django_logic.commands import BaseCommand
from flowback.decidables.fields import DecidableStateChoices
from flowback.decidables.models import Decidable
from flowback.group import rules as group_rules

class Permissions(BaseCommand):
    def execute(self, state, user, **kwargs):
        return user is None or all(command(user, state.instance, **kwargs) for command in self._commands)


class DecidableProcess(BaseProcess):
    process_name='fsm'
    permission_class = Permissions
    states = DecidableStateChoices
    
    transitions = [
        Transition(
            action_name='start_poll',
            sources=['not_started'],
            target='open'
        ),
        Transition(
            action_name='restart_poll',
            sources=['closed'],
            target='open'
        ),
        Transition(
            action_name='end_poll',
            sources=['open'],
            target='closed'
        )
    ]

ProcessManager.bind_model_process(
    Decidable,
    DecidableProcess,
    state_field='state'
)