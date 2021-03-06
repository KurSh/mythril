from mythril.analysis.report import Issue
from laser.ethereum.svm import NodeFlags
import logging
import re


'''
MODULE DESCRIPTION:

Test whether CALL return value is checked.

For direct calls, the Solidity compiler auto-generates this check. E.g.:

    Alice c = Alice(address);
    c.ping(42);

Here the CALL will be followed by IZSERO(retval), if retval = ZERO then state is reverted.

For low-level-calls this check is omitted. E.g.:

    c.call.value(0)(bytes4(sha3("ping(uint256)")),1);

'''


def execute(statespace):

    logging.debug("Executing module: UNCHECKED_RETVAL")

    issues = []

    for k in statespace.nodes:

        node = statespace.nodes[k]

        if NodeFlags.CALL_RETURN in node.flags:

            retval_checked = False

            for state in node.states:

                instr = state.get_current_instruction()

                if (instr['opcode'] == 'ISZERO' and re.search(r'retval', str(state.mstate.stack[-1]))):
                    retval_checked = True
                    break

            if not retval_checked:

                address = state.get_current_instruction()['address']
                issue = Issue(node.contract_name, node.function_name, address, "Unchecked CALL return value")

                issue.description = \
                    "The return value of an external call is not checked. Note that the contract will continue if the call fails."

                issues.append(issue)

        else:

            nStates = len(node.states)

            for idx in range(0, nStates):

                state = node.states[idx]
                instr = state.get_current_instruction()

                if (instr['opcode'] == 'CALL'):

                    retval_checked = False

                    for _idx in range(idx, idx + 10):

                        try:
                            _state = node.states[_idx]
                            _instr = _state.get_current_instruction()

                            if (_instr['opcode'] == 'ISZERO' and re.search(r'retval', str(_state .mstate.stack[-1]))):
                                retval_checked = True
                                break

                        except IndexError:
                            break

                    if not retval_checked:

                        address = instr['address']
                        issue = Issue(node.contract_name, node.function_name, address, "Unchecked CALL return value")

                        issue.description = \
                            "The return value of an external call is not checked. Note that execution continue even if the called contract throws."

                        issues.append(issue)

    return issues
