# -*- encoding: utf-8 -*-
import json

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from service import coletor_dados
from django.http import Http404

# Create your views here.
#Members.objects.values('designation').annotate(dcount=Count('designation'))
from sistema.formulario import formulario_login, formulario_register
from sistema.models import Repositorio, Projeto


def login_view(request):
    if (request.method == "POST"):
        #print "Tentando salvar..",request.POST

        formulario = formulario_login(request.POST)

        if formulario.is_valid():
            usuario = formulario.cleaned_data['usuario']
            senha = formulario.cleaned_data['senha']
            #print "Olha a senha: ",senha," - ",usuario

            try:
                user_por_email = User.objects.get(email=usuario)
            except:
                user_por_email = None
            #print "Achei o user:",user_por_email

            if user_por_email != None:
                user = authenticate(username=user_por_email, password=senha)
                if user is not None:
                    if user.is_active:
                        #print "Logando.."
                        login(request,user)
                        return HttpResponseRedirect('/')
                    else:
                        msg = "Sua conta está desabilitada, entre em contato com o administrador do sistema."
                        messages.add_message(request, messages.SUCCESS, msg)

                else:
                    msg = "Email ou senha estão incorretas!"
                    print msg

            else:
                msg = "Conta de email não cadastrada!"
                print msg

        else:
            #print "Olha a senha: ", formulario['senha'], " - ", formulario['usuario']
            msg = verificar_erros_formulario(formulario)
            print "ERRO:",msg


        messages.add_message(request, messages.SUCCESS, msg)
        return render_to_response("usuario/login.html", {'formulario': formulario},context_instance=RequestContext(request))

    else:
        formulario = formulario_login()
        return render_to_response("usuario/login.html",{'formulario':formulario },context_instance=RequestContext(request))

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')

def profile_page(request):
    user = User.objects.get(username__exact=str(request.user))
    user_repositories = Repositorio.objects.filter(proprietario=user)
    for item in user_repositories:
        item.projetos = Projeto.objects.filter(repositorio=item)
    return render_to_response("usuario/profile.html",{'meus_repositorios': user_repositories},
                              context_instance=RequestContext(request))

def update_project_monitored(request):
    if request.is_ajax():
        project_id = int(request.POST['id_project'])
        if request.POST['monitorar'] == "true":
            monitorar = True
        else:
            monitorar = False
        projeto = Projeto.objects.get(pk=project_id)
        projeto.monitorado = monitorar
        projeto.save()
        return HttpResponse(json.dumps({"message": "Registro Salvo com sucesso"}))

    else:
        raise Http404

def get_monitored_projects(request):
    user = User.objects.get(username__exact=str(request.user))
    user_repositories = Repositorio.objects.filter(proprietario=user)
    response_dict = []
    for item in user_repositories:
        item.projetos = Projeto.objects.filter(repositorio=item)
        object = {'repositorio': item.nome_repositorio}
        list_proj = []
        for proj in item.projetos:
            list_proj.append({'id':proj.id,'projeto':proj.nome_projeto,'monitorado':proj.monitorado})
        object['projetos'] = list_proj
        response_dict.append(object)
    return HttpResponse(json.dumps(response_dict))

def profile_view(request):
    nome_usuario = str(request.user)
    usuario = User.objects.get(username__exact=nome_usuario)

    if (request.method == "POST"):
        if 'adicionar_repositorio' in request.POST:
            nome_repositorio = request.POST['nome_repositorio']
            url_repositorio = request.POST['url_repositorio']
            if url_repositorio[-1] != '/':
                url_repositorio = url_repositorio + "/"

            projetos_disponiveis = coletor_dados().coletar_dados_repositorio(url_repositorio)
            total_projeto = len(projetos_disponiveis)

            if usuario != None:
                novo_repositorio = Repositorio(
                    url= url_repositorio,
                    nome_repositorio = nome_repositorio.upper(),
                    total_projetos = total_projeto,
                    proprietario = usuario
                )

                novo_repositorio.save()

                for item in projetos_disponiveis:
                    novo_projeto = Projeto(
                        nome_projeto= item[0].upper(),
                        linguagem =item[1].upper(),
                        url_projeto = item[2],
                        repositorio = novo_repositorio
                    )

                    novo_projeto.save()

        meus_repositorios = Repositorio.objects.filter(proprietario=usuario)

    else:
        meus_repositorios = Repositorio.objects.filter(proprietario=usuario)

        meus_repo = []
        for item in meus_repositorios:
            item.projetos = Projeto.objects.filter(repositorio=item)

        #print "Veja: ",meus_repositorios[0].projetos
        projetos_disponiveis = None
    #    formulario = formulario_register(request.POST)
    #else:
    return render_to_response("usuario/profile.html", {'meus_repositorios':meus_repositorios,'projetos_disponiveis':projetos_disponiveis,'formulario': None},
                                      context_instance=RequestContext(request))

def register_view(request):
    if (request.method == "POST"):
        formulario = formulario_register(request.POST)
        if formulario.is_valid():
            email = formulario.cleaned_data['usuario']
            senha = formulario.cleaned_data['senha']
            confirme_senha = formulario.cleaned_data['confirme_senha']

            print "SENHAS:",senha, confirme_senha,"=>", senha == confirme_senha
            if senha == confirme_senha:

                try:
                    user_por_email = User.objects.get(email=email)
                except:
                    user_por_email = None

                if user_por_email == None:
                    usuario = criar_usuario(email, senha)
                    print "olha o user antes:", usuario
                    user_autenticate = authenticate(username=usuario, password=senha)
                    print "olha o user depois:",user_autenticate
                    if user_autenticate is not None:
                        if user_autenticate.is_active:
                            print "Logando.."
                            login(request, user_autenticate)
                            return HttpResponseRedirect('/')
                        else:
                            msg = "Erro! Sua conta está desabilitada, entre em contato com o administrador do sistema."
                            messages.add_message(request, messages.SUCCESS, msg)

                    else:
                        msg = "Email ou senha estão incorretas!"
                        print msg

                else:
                    msg = "Erro! Conta de email já cadastrada."
                    print msg

            else:
                msg = "Erro! Senhas não conferem."
                print msg
                formulario = formulario_register(initial={
                    'usuario':email,
                    'senha': senha,
                    'confirme_senha':confirme_senha
                })

        else:
            #print "Olha a senha: ", formulario['senha'], " - ", formulario['usuario']
            msg = verificar_erros_formulario(formulario)
            print "ERRO:", msg

        messages.add_message(request, messages.SUCCESS, msg)
        #print formulario['senha'],"SENHAS ULTIMO:", senha, confirme_senha, "=>", senha == confirme_senha
        return render_to_response("usuario/register.html", {'formulario': formulario},context_instance=RequestContext(request))

    else:
        formulario = formulario_register(request.POST)
        return render_to_response("usuario/register.html", {'formulario': formulario},
                                  context_instance=RequestContext(request))



def criar_usuario(email,senha):
    user = User()
    user.email = email
    user.set_password(senha)
    user.username = email
    user.save()
    return user

def verificar_erros_formulario(formulario):
    msg = ""
    for campo in formulario:
        erros = campo.errors.as_data()

        if erros != []:

            erro = erros[0][0]

            if 'email' in erro:
                msg = "Erro! " + unicode(erro)

            elif 'data' in erro:
                msg = "Erro! " + unicode(erro)

            else:
                msg = campo.label + " " + unicode(erro)

            return msg