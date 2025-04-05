import tomllib
import platformdirs
import click
import pathlib
from functools import wraps


def _get_meta_key_name(name=None):
    return f"config.{name}" if name else "config"


def _is_cli_specified(ctx, optionname):
    return ctx.get_parameter_source(optionname) not in (
        click.core.ParameterSource.DEFAULT,
        click.core.ParameterSource.DEFAULT_MAP,
    )


def _get_config_path_for_command(ctx):
    if ctx.parent is not None:
        ancestry = _get_config_path_for_command(ctx.parent)
        ancestry.append(ctx.command.name)
    else:
        ancestry = [ctx.command.name]

    return ancestry


class ConfigFileOption(click.core.Option):
    """A wrapper class to help identify the config option"""

    pass


def config_file_option(
    *param_decls,
    name=None,
    paths=None,
    filename="config.toml",
    parser=tomllib.load,
    **option_args,
):
    if param_decls and callable(param_decls[0]):
        # The decorator was called without parentheses,
        # so it is just a wrapper, not a factory (see below)
        fn = param_decls[0]
        param_decls = None
    else:
        # … and in this case it is a factory. See bottom for
        # return value.
        fn = None

    param_decls = param_decls or ("--config", "-c")
    option_args.setdefault("help", "Config file to read")
    option_args["type"] = click.Path(path_type=pathlib.Path)
    option_args["multiple"] = True

    def decorator(fn):
        @click.option(*param_decls, **option_args, cls=ConfigFileOption)
        @click.pass_context
        @wraps(fn)
        def wrapper(ctx, *cli_args, **cli_kwargs):

            config_opt = None
            for param in ctx.command.get_params(ctx):
                if isinstance(param, ConfigFileOption):
                    config_opt = param
                    break

            assert config_opt is not None, "Could not find config option"

            if _is_cli_specified(ctx, config_opt.name):
                cfgpaths = cli_kwargs.get(config_opt.name) or []

            else:
                cfgpaths = (
                    [pathlib.Path(cfgf) for cfgf in paths]
                    if paths is not None
                    else [
                        platformdirs.user_config_path(ctx.command.name)
                        / filename
                    ]
                )

            for path in cfgpaths:
                try:
                    with open(path, "rb") as f:
                        cfg = parser(f)
                    if cfg is not None:
                        break

                except FileNotFoundError:
                    pass
            else:
                cfg = None
                path = None

            ctx.meta[_get_meta_key_name(name)] = config_opt.name, cfg, path
            ctx.params[config_opt.name] = cfg

            return fn(*cli_args, **cli_kwargs)

        return wrapper

    if fn is not None:
        return decorator(fn)

    return decorator


def merge_config(name=None, cfgpath=None, cli_over_config=True):
    # if the decorator is called without parentheses, the argument
    # is actually a callable, and further down we outright invoke
    # the decorator factory to return the actual decorator
    if callable(name):
        fn = name
        name = None
    else:
        fn = None

    def decorator(fn):
        @click.pass_context
        @wraps(fn)
        def wrapper(ctx, *cli_args, **cli_kwargs):

            optname, cfg, path = ctx.meta.get(
                _get_meta_key_name(name), (None, {}, None)
            )

            cfgpath = _get_config_path_for_command(ctx)[1:]
            for key in cfgpath:
                cfg = cfg.get(key, {})

            for param in ctx.command.params:
                if _is_cli_specified(ctx, param.name) and cli_over_config:
                    continue

                elif cfg and (value := cfg.get(param.name)):
                    try:
                        cli_kwargs[param.name] = param.process_value(ctx, value)
                    except click.BadParameter as err:
                        raise click.ClickException(
                            f"In {path}, key '{'.'.join(cfgpath)}': "
                            f"{err.message}"
                        )
                    else:
                        ctx.set_parameter_source(
                            param.name, f"config file {name}"
                        )

            return fn(*cli_args, **cli_kwargs)

        return wrapper

    if fn is not None:
        return decorator(fn)

    return decorator
